#!/usr/bin/env python3
"""
Script to generate and verify environment variables for Render.com deployment.
This helps fix authentication issues with GitHub repositories.

Usage: python render_env_setup.py
"""

import os
import subprocess
import getpass
import sys

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def get_current_remote_url():
    """Get the current Git remote URL"""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'], 
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def test_authentication(url, username, token):
    """Test if authentication works for the given URL and credentials"""
    if not url.startswith('https://'):
        return False, "URL must start with https://"
    
    # Create authenticated URL
    auth_url = url.replace('https://', f'https://{username}:{token}@')
    
    # Test connection
    try:
        result = subprocess.run(
            ['git', 'ls-remote', auth_url], 
            capture_output=True, 
            text=True,
            check=True
        )
        return True, "Authentication successful"
    except subprocess.CalledProcessError as e:
        return False, f"Authentication failed: {e.stderr}"

def main():
    print_banner("Render.com Environment Setup for GitHub Authentication")
    
    # Get current repository URL
    current_url = get_current_remote_url()
    if current_url:
        print(f"Current Git remote URL: {current_url}")
        repo_url = current_url
    else:
        print("No Git remote URL found.")
        repo_url = input("Enter your GitHub repository URL (https://github.com/username/repo.git): ")
    
    # Get GitHub username
    github_username = input("Enter your GitHub username: ")
    
    # Get GitHub token securely
    github_token = getpass.getpass("Enter your GitHub Personal Access Token (hidden input): ")
    
    # Test authentication
    print("\nTesting authentication...")
    success, message = test_authentication(repo_url, github_username, github_token)
    
    if success:
        print("✅ Authentication successful! Your credentials work with this repository.")
    else:
        print(f"❌ Authentication failed: {message}")
        print("\nPossible issues:")
        print("1. The personal access token doesn't have the correct permissions")
        print("2. The username is incorrect")
        print("3. The repository doesn't exist or you don't have access to it")
        print("4. The repository URL is incorrect")
        
        print("\nTo fix:")
        print("1. Make sure the repository exists at", repo_url)
        print("2. Generate a new personal access token with 'repo' scope")
        print("3. Check your GitHub username")
        print("4. Make sure you have access to the repository")
        
        return 1
    
    # Generate Render.com environment variables
    print_banner("Render.com Environment Variables")
    print("Add these variables to your Render.com service:")
    print("\nGIT_REPO_URL=" + repo_url)
    print("GIT_USERNAME=" + github_username)
    print("GIT_TOKEN=" + github_token[:4] + "..." + "(shown partially for security)")
    
    # Instructions for setting up on Render
    print_banner("Setup Instructions")
    print("1. Go to the Render Dashboard: https://dashboard.render.com")
    print("2. Select your AwaazTimetable service")
    print("3. Go to 'Environment' tab")
    print("4. Add the environment variables listed above")
    print("5. Click 'Save Changes'")
    print("6. Redeploy your service\n")
    
    # Option to update local Git remote
    update_local = input("Would you like to update your local Git remote with these credentials? (y/n): ")
    if update_local.lower() == 'y':
        auth_url = repo_url.replace('https://', f'https://{github_username}:{github_token}@')
        try:
            subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], check=True)
            print("✅ Local Git remote updated successfully with authentication!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to update Git remote: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 