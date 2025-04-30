#!/usr/bin/env python3
"""
Test script to verify Git repository connection and push capability.
This should be run from the command line with necessary environment variables:

Example:
GIT_REPO_URL=https://github.com/yourusername/AwaazTimetable.git \
GIT_USERNAME=yourusername \
GIT_TOKEN=your_personal_access_token \
python test_git_connection.py

IMPORTANT: Before running this script, make sure:
1. The repository exists on GitHub (create it if it doesn't exist)
2. You have the correct access permissions to the repository
3. Your GIT_TOKEN has the necessary permissions to push to the repository
"""

import os
import sys
import subprocess
import datetime

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, '='))
    print("=" * 80)

def run_command(cmd, exit_on_error=False):
    """Run a command and return output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"Output: {result.stdout}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running '{cmd}':")
        print(f"  Exit code: {e.returncode}")
        print(f"  Error output: {e.stderr}")
        if exit_on_error:
            print("Exiting due to error.")
            sys.exit(1)
        return None

def main():
    print_header("GIT REMOTE REPOSITORY CONNECTION TEST")
    
    # Check if necessary environment variables are set
    git_repo_url = os.environ.get('GIT_REPO_URL')
    git_username = os.environ.get('GIT_USERNAME')
    git_token = os.environ.get('GIT_TOKEN')
    
    if not git_repo_url:
        print("ERROR: GIT_REPO_URL environment variable not set.")
        print("Please set this to your remote repository URL (e.g., https://github.com/username/repo.git)")
        return 1
    
    print(f"Repository URL: {git_repo_url}")
    print(f"Git Username: {git_username or 'Not set'}")
    print(f"Git Token: {'Provided' if git_token else 'Not set'}")
    
    print_header("CHECKING GIT INSTALLATION")
    git_version = run_command("git --version")
    if not git_version:
        print("ERROR: Git is not installed or not in PATH.")
        return 1
    
    print_header("CHECKING CURRENT GIT CONFIG")
    run_command("git config --list")
    
    print_header("SETTING UP GIT USER")
    run_command(f"git config user.name \"{git_username or 'Awaaz Timetable App'}\"")
    run_command(f"git config user.email \"{os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')}\"")
    
    print_header("SETTING UP REMOTE")
    remotes = run_command("git remote")
    if "origin" in remotes.split():
        print("Remote 'origin' already exists. Updating...")
        
        # Format URL with credentials if provided
        if git_username and git_token and git_repo_url.startswith('https://'):
            auth_url = git_repo_url.replace('https://', f'https://{git_username}:{git_token}@')
            run_command(f"git remote set-url origin \"{auth_url}\"")
        else:
            run_command(f"git remote set-url origin \"{git_repo_url}\"")
    else:
        print("Adding remote 'origin'...")
        # Format URL with credentials if provided
        if git_username and git_token and git_repo_url.startswith('https://'):
            auth_url = git_repo_url.replace('https://', f'https://{git_username}:{git_token}@')
            run_command(f"git remote add origin \"{auth_url}\"")
        else:
            run_command(f"git remote add origin \"{git_repo_url}\"")
    
    print_header("TESTING REMOTE CONNECTION")
    fetch_result = run_command("git fetch origin")
    if fetch_result is None:
        print("ERROR: Unable to fetch from remote. Check your credentials and connection.")
        return 1
    
    print_header("CREATING TEST FILE")
    test_file = "git_test.txt"
    with open(test_file, 'w') as f:
        f.write(f"Git connection test file\n")
        f.write(f"Created at: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Testing remote connection to: {git_repo_url}\n")
    
    print_header("COMMITTING TEST FILE")
    run_command(f"git add {test_file}")
    run_command(f"git commit -m \"Test commit for remote connection\"")
    
    print_header("PUSHING TO REMOTE")
    # Get current branch name
    branch_name = run_command("git branch --show-current") or "main"
    print(f"Current branch: {branch_name}")
    
    # Try to push with tracking
    push_result = run_command(f"git push -u origin {branch_name}")
    if push_result is None:
        print("ERROR: Failed to push to remote repository.")
        return 1
    
    print_header("SUCCESS")
    print("Git remote repository connection test was successful!")
    print("Your application should now be able to push changes to the remote repository.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 