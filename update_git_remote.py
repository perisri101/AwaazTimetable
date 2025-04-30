#!/usr/bin/env python3
"""
Script to update Git remote URL and configuration.
Use this script to fix the 'Repository not found' error by updating the remote repository URL.

Usage:
    python update_git_remote.py --url https://github.com/username/repo.git [--username USERNAME] [--token TOKEN]

Options:
    --url URL          New Git repository URL
    --username USER    GitHub username (optional)
    --token TOKEN      GitHub personal access token (optional)

Example:
    python update_git_remote.py --url https://github.com/your-username/AwaazTimetable.git --username your-username --token your-token
"""

import argparse
import os
import subprocess
import sys

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def run_command(cmd, exit_on_error=False):
    """Run a command and return its output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return None

def main():
    parser = argparse.ArgumentParser(description='Update Git remote URL and configuration')
    parser.add_argument('--url', required=True, help='New Git repository URL')
    parser.add_argument('--username', help='GitHub username')
    parser.add_argument('--token', help='GitHub personal access token')
    args = parser.parse_args()

    print_banner("Git Remote Update Tool")
    
    # Check current remote configuration
    print_banner("Current Remote Configuration")
    run_command("git remote -v")
    
    # Update remote URL
    print_banner("Updating Remote URL")
    if args.username and args.token and args.url.startswith('https://'):
        # Create authenticated URL with credentials
        auth_url = args.url.replace('https://', f'https://{args.username}:{args.token}@')
        print(f"Using authenticated URL with credentials (token hidden)")
        run_command(f'git remote set-url origin "{auth_url}"')
    else:
        # Use plain URL
        run_command(f'git remote set-url origin "{args.url}"')
    
    # Verify update
    print_banner("Updated Remote Configuration")
    run_command("git remote -v")
    
    # Test connection
    print_banner("Testing Connection to Remote")
    fetch_result = run_command("git fetch origin")
    if fetch_result is not None:
        print("✅ Successfully connected to remote repository!")
        # Get remote branches
        run_command("git branch -r")
    else:
        print("❌ Failed to connect to remote repository!")
        print("\nPossible issues:")
        print("1. The repository doesn't exist on GitHub")
        print("2. You don't have access permissions")
        print("3. The authentication credentials are incorrect")
        print("\nSolutions:")
        print("1. Create the repository on GitHub first")
        print("2. Use a Personal Access Token with appropriate permissions")
        print("3. Double-check the URL for typos")
    
    # Render.com configuration instructions
    print_banner("Render.com Configuration Instructions")
    print("To fix the issue on Render.com, you need to set these environment variables:")
    print("\n1. GIT_REPO_URL=" + args.url)
    if args.username:
        print("2. GIT_USERNAME=" + args.username) 
    else:
        print("2. GIT_USERNAME=your-github-username")
    if args.token:
        print("3. GIT_TOKEN=" + args.token[:4] + "..." + "(token masked for security)")
    else:
        print("3. GIT_TOKEN=your-github-personal-access-token")
    
    print("\nTo set these on Render.com:")
    print("1. Go to the Render Dashboard")
    print("2. Select your service")
    print("3. Go to 'Environment' tab")
    print("4. Add these environment variables")
    print("5. Click 'Save Changes' and redeploy your service")

if __name__ == "__main__":
    main() 