#!/usr/bin/env python3
"""
Diagnostic and fix script for Git connection issues.
This script will:
1. Run a diagnostic on your Git repository
2. Verify if the repository exists
3. Test authentication credentials
4. Fix common connection issues
5. Update Render.com environment configuration

Usage: python fix_git_connection.py
"""

import os
import sys
import subprocess
import getpass
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def run_command(cmd, exit_on_error=False, show_output=True):
    """Run a command and return its output"""
    if show_output:
        print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if show_output and result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"Error: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return e.stderr.strip() if e.stderr else "", False

def check_repository_exists(repo_url, username=None, token=None):
    """Check if a GitHub repository exists and is accessible"""
    # Extract owner and repo name from URL
    # Format: https://github.com/username/repo.git
    if not repo_url.startswith('https://github.com/'):
        return False, "URL is not a valid GitHub repository URL"
    
    parts = repo_url.replace('https://github.com/', '').split('/')
    if len(parts) < 2:
        return False, "URL format is incorrect"
    
    owner = parts[0]
    repo_name = parts[1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    
    # Use GitHub API to check if repo exists
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    headers = {
        'User-Agent': 'AwaazTimetable-App'
    }
    
    # Add authentication if provided
    if username and token:
        auth = f"{username}:{token}"
        import base64
        auth_header = base64.b64encode(auth.encode()).decode()
        headers['Authorization'] = f"Basic {auth_header}"
    
    try:
        req = Request(api_url, headers=headers)
        response = urlopen(req)
        data = json.loads(response.read().decode())
        return True, f"Repository exists: {data.get('full_name')} - {data.get('description')}"
    except HTTPError as e:
        if e.code == 404:
            return False, f"Repository '{owner}/{repo_name}' does not exist or is not accessible"
        elif e.code == 401:
            return False, "Authentication failed - invalid credentials"
        else:
            return False, f"Error checking repository: HTTP {e.code}"
    except URLError as e:
        return False, f"Error connecting to GitHub: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print_banner("Git Connection Diagnostics and Fix Tool")
    
    # Step 1: Check current Git setup
    print_banner("Checking Current Git Setup")
    
    # Get current remote URL
    remote_url, success = run_command("git config --get remote.origin.url")
    if not success or not remote_url:
        print("No Git remote URL configured.")
        repo_url = input("Enter your GitHub repository URL (https://github.com/username/repo.git): ")
    else:
        print(f"Current remote URL: {remote_url}")
        repo_url = remote_url
    
    # Normalize URL (remove credentials if present)
    if '@' in repo_url:
        repo_url = 'https://' + repo_url.split('@')[1]
    
    # Step 2: Check if repository exists
    print_banner("Checking If Repository Exists")
    
    # Get GitHub credentials
    github_username = input("Enter your GitHub username: ")
    github_token = getpass.getpass("Enter your GitHub Personal Access Token (hidden input): ")
    
    exists, message = check_repository_exists(repo_url, github_username, github_token)
    
    if exists:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        
        create_repo = input("\nWould you like to create this repository on GitHub? (y/n): ")
        if create_repo.lower() == 'y':
            print("\nTo create a new repository on GitHub:")
            print(f"1. Go to: https://github.com/new")
            print(f"2. Repository name: {repo_url.split('/')[-1].replace('.git', '')}")
            print(f"3. Choose visibility (Public or Private)")
            print(f"4. Create repository")
            
            print("\nAfter creating the repository on GitHub, press Enter to continue...")
            input()
    
    # Step 3: Configure authentication
    print_banner("Configuring Git Authentication")
    
    # Update Git configuration
    run_command(f"git config user.name \"{github_username}\"")
    run_command(f"git config user.email \"{github_username}@users.noreply.github.com\"")
    
    # Create authenticated remote URL
    auth_url = repo_url.replace('https://', f'https://{github_username}:{github_token}@')
    
    # Update or add remote
    remotes, _ = run_command("git remote")
    if 'origin' in remotes.split():
        print("Updating existing remote 'origin'...")
        run_command(f"git remote set-url origin \"{auth_url}\"")
    else:
        print("Adding new remote 'origin'...")
        run_command(f"git remote add origin \"{auth_url}\"")
    
    # Test connection
    print_banner("Testing Connection")
    output, success = run_command("git fetch origin", show_output=False)
    
    if success:
        print("✅ Successfully connected to remote repository!")
        
        # Try to push
        print_banner("Testing Push")
        
        # Create test file
        with open('git_connection_test.txt', 'w') as f:
            f.write(f"Git connection test file\n")
        
        run_command("git add git_connection_test.txt")
        run_command("git commit -m \"Test connection to remote repository\"")
        
        output, push_success = run_command("git push -u origin HEAD", show_output=False)
        
        if push_success:
            print("✅ Successfully pushed to remote repository!")
        else:
            print("❌ Push failed. Error:")
            print(output)
            
            if "branch is behind" in output or "non-fast-forward" in output:
                print("\nTrying to pull and push again...")
                run_command("git pull --rebase origin HEAD")
                output, push_success = run_command("git push -u origin HEAD", show_output=False)
                
                if push_success:
                    print("✅ Successfully pushed to remote repository after pull!")
                else:
                    print("❌ Push still failed after pull.")
    else:
        print("❌ Failed to connect to remote repository.")
        print("Error:")
        print(output)
    
    # Step 4: Render.com environment configuration
    print_banner("Render.com Environment Configuration")
    print("Add these environment variables to your Render.com service:")
    print("\nGIT_REPO_URL=" + repo_url)
    print("GIT_USERNAME=" + github_username)
    print("GIT_TOKEN=" + github_token[:4] + "..." + "(token masked for security)")
    
    print("\nTo set these on Render.com:")
    print("1. Go to the Render Dashboard: https://dashboard.render.com")
    print("2. Select your AwaazTimetable service")
    print("3. Go to 'Environment' tab")
    print("4. Add these environment variables")
    print("5. Click 'Save Changes'")
    print("6. Redeploy your service")
    
    # Clean up test file
    if os.path.exists('git_connection_test.txt'):
        os.remove('git_connection_test.txt')
    
    print_banner("Summary")
    print("1. Repository Exists: " + ("Yes" if exists else "No - Create it on GitHub"))
    print("2. Git Authentication: Configured")
    print("3. Connection Test: " + ("Successful" if success else "Failed"))
    print("4. Push Test: " + ("Successful" if 'push_success' in locals() and push_success else "Failed"))
    print("5. Render.com Environment: Configuration instructions provided")

if __name__ == "__main__":
    main() 