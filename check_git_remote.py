#!/usr/bin/env python3
"""
Script to check git remote details and repository URL.
This helps verify which repository is being used for Git operations.

Usage: python check_git_remote.py
"""

import os
import subprocess
import sys
import re

def print_banner(message):
    """Print a formatted banner message"""
    banner = "\n" + "=" * 80 + "\n" + " " + message.center(78) + " \n" + "=" * 80
    print(banner)

def run_command(cmd):
    """Run a command and return its output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Output: {result.stdout}")
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return e.stderr.strip() if e.stderr else "", False

def check_git_remote():
    """Check Git remote details"""
    print_banner("GIT REMOTE DETAILS")
    
    # Get all remotes
    remotes, success = run_command("git remote -v")
    if not success or not remotes:
        print("No Git remotes configured!")
        return
    
    # Extract and print remote details
    print("\nFormatted Remote Details:")
    print("-------------------------")
    
    for line in remotes.split('\n'):
        parts = line.split()
        if len(parts) >= 3:
            name = parts[0]
            url = parts[1]
            
            # Mask sensitive information in the URL
            masked_url = url
            if '@' in url:
                # For SSH or HTTPS with embedded credentials
                match = re.match(r'(https?://)([^@]+)@(.+)', url)
                if match:
                    protocol, credentials, path = match.groups()
                    masked_url = f"{protocol}***:***@{path}"
            
            print(f"Name: {name}, URL: {masked_url}, Type: {parts[2]}")
    
    # Get specific details about origin
    print_banner("ORIGIN DETAILS")
    origin_url, _ = run_command("git config --get remote.origin.url")
    
    # Try to extract repo owner and name
    print("\nRepository Information:")
    print("-------------------------")
    
    # Extract owner and repo name from different URL formats
    owner = None
    repo = None
    
    # Handle different URL formats
    if 'github.com' in origin_url:
        if origin_url.startswith('https://'):
            # HTTPS URL
            match = re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$', origin_url)
            if match:
                owner, repo = match.groups()
        elif origin_url.startswith('git@'):
            # SSH URL
            match = re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$', origin_url)
            if match:
                owner, repo = match.groups()
    
    if owner and repo:
        print(f"Owner: {owner}")
        print(f"Repository: {repo}")
        print(f"Expected GitHub URL: https://github.com/{owner}/{repo}")
    else:
        print(f"Could not parse owner/repo from URL: {origin_url}")
    
    # Check environment variables
    print_banner("ENVIRONMENT VARIABLES")
    repo_url = os.environ.get('GIT_REPO_URL')
    if repo_url:
        print(f"GIT_REPO_URL: {repo_url}")
        
        # Check if GIT_REPO_URL matches the configured remote
        if repo_url == origin_url:
            print("✅ GIT_REPO_URL matches the configured remote URL")
        else:
            print("❌ GIT_REPO_URL does NOT match the configured remote URL")
            
            # Try to identify differences
            print("\nDifferences:")
            if 'github.com' in repo_url and 'github.com' in origin_url:
                repo_url_parts = re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$', repo_url)
                origin_parts = re.search(r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$', origin_url)
                
                if repo_url_parts and origin_parts:
                    repo_owner, repo_name = repo_url_parts.groups()
                    origin_owner, origin_name = origin_parts.groups()
                    
                    if repo_owner != origin_owner:
                        print(f"  - Different owner: {repo_owner} (env) vs {origin_owner} (configured)")
                    if repo_name != origin_name:
                        print(f"  - Different repository: {repo_name} (env) vs {origin_name} (configured)")
    else:
        print("GIT_REPO_URL environment variable is not set")
    
    # Check head
    print_banner("CURRENT HEAD")
    run_command("git log -1 --oneline")
    
    # Check branches
    print_banner("LOCAL BRANCHES")
    run_command("git branch")
    
    print_banner("REMOTE BRANCHES")
    run_command("git branch -r")

def check_last_commit():
    """Check details about the last commit"""
    print_banner("LAST COMMIT DETAILS")
    
    # Get last commit info
    last_commit, success = run_command("git log -1 --stat")
    if not success or not last_commit:
        print("Could not get last commit info!")
        return
    
    # Check if the commit was pushed to remote
    print_banner("PUSH STATUS")
    status, _ = run_command("git cherry -v")
    
    if status:
        print("\nUnpushed commits:")
        print(status)
        print("\n❌ There are commits that have not been pushed to the remote repository")
    else:
        print("✅ All commits have been pushed to the remote repository")
    
    # Get the diff between local and remote
    print_banner("LOCAL VS REMOTE")
    diff, _ = run_command("git diff origin/main...HEAD --name-status")
    
    if diff:
        print("\nDifferences between local and remote (origin/main):")
        print(diff)
    else:
        print("✅ Local and remote are in sync")

def main():
    print_banner("GIT REPOSITORY DIAGNOSTIC")
    
    # Get working directory
    cwd = os.getcwd()
    print(f"Working directory: {cwd}")
    
    # Check if in Git repository
    git_dir, success = run_command("git rev-parse --git-dir")
    if not success:
        print("Not in a Git repository!")
        return 1
    
    print(f"Git directory: {git_dir}")
    
    # Check remote details
    check_git_remote()
    
    # Check last commit
    check_last_commit()
    
    # Summary
    print_banner("FIX SUGGESTIONS")
    print("""If your push succeeded but files are not showing on GitHub:
    
1. Check if you're looking at the correct repository on GitHub
2. Make sure you're viewing the correct branch (usually 'main')
3. Try fetching and pulling in your local repository to see the changes
4. Check if the GIT_REPO_URL environment variable matches the actual GitHub URL
5. Try running 'git push -f origin main' on Render to force push (only if needed)
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 