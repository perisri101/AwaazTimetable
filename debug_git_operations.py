#!/usr/bin/env python3
"""
Real-time Git operations monitoring script for AwaazTimetable

This script monitors Git operations in real-time, showing detailed information
about each operation, including:
- Commands executed
- Results/output
- Error messages
- Environment variables
- Git configuration
- Repository status

It's a valuable tool for debugging Git-related issues in the AwaazTimetable
application, especially when running on remote servers like Render.com.

Usage: python debug_git_operations.py [--verbose] [--test-push]

Options:
    --verbose    Show detailed output for all Git operations
    --test-push  Perform a test push operation
"""

import os
import sys
import subprocess
import argparse
import time
import json
import threading
import tempfile
from pathlib import Path
from datetime import datetime

# Constants
DATA_DIR = "data"
REQUIRED_ENV_VARS = ["GIT_REPO_URL", "GIT_USERNAME", "GIT_TOKEN"]

# Color formatting for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner(message):
    """Print a formatted banner message"""
    width = 80
    print(f"\n{Colors.HEADER}{'-' * width}")
    print(f" {message} ".center(width))
    print(f"{'-' * width}{Colors.ENDC}\n")

def run_command(cmd, exit_on_error=False):
    """Run a command and return its output"""
    print(f"{Colors.CYAN}Running: {cmd}{Colors.ENDC}")
    try:
        start_time = time.time()
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.stdout.strip():
            print(f"{Colors.GREEN}--- Output ---{Colors.ENDC}")
            print(result.stdout.strip())
        
        print(f"{Colors.GREEN}Command completed successfully in {duration:.2f}s{Colors.ENDC}")
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}--- Error ---{Colors.ENDC}")
        print(f"Exit code: {e.returncode}")
        
        if e.stderr:
            print(f"{Colors.FAIL}Error output:{Colors.ENDC}")
            print(e.stderr)
        
        if exit_on_error:
            print(f"{Colors.FAIL}Exiting due to error.{Colors.ENDC}")
            sys.exit(1)
        return e.stderr.strip() if e.stderr else "", False

def check_env_variables():
    """Check if required environment variables are set"""
    print_banner("Checking Environment Variables")
    
    missing_vars = []
    
    for var in REQUIRED_ENV_VARS:
        value = os.environ.get(var)
        if not value:
            print(f"{Colors.FAIL}❌ {var}: Not set{Colors.ENDC}")
            missing_vars.append(var)
        else:
            # Mask token for security
            if var == 'GIT_TOKEN':
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                print(f"{Colors.GREEN}✓ {var}: {masked_value}{Colors.ENDC}")
            else:
                print(f"{Colors.GREEN}✓ {var}: {value}{Colors.ENDC}")
    
    if missing_vars:
        print(f"\n{Colors.WARNING}Missing environment variables: {', '.join(missing_vars)}{Colors.ENDC}")
        
        # Offer to set temporary variables for this session
        set_vars = input("\nWould you like to set these variables temporarily for this session? (y/n): ")
        if set_vars.lower() == 'y':
            for var in missing_vars:
                if var == 'GIT_TOKEN':
                    # Don't echo the token when typing
                    import getpass
                    value = getpass.getpass(f"Enter {var} (input hidden): ")
                else:
                    value = input(f"Enter {var}: ")
                os.environ[var] = value
            
            # Recheck after setting
            check_env_variables()
    
    # Validate URL format
    repo_url = os.environ.get('GIT_REPO_URL', '')
    if repo_url and not repo_url.startswith('https://github.com/'):
        print(f"{Colors.WARNING}Warning: GIT_REPO_URL doesn't follow the standard format.{Colors.ENDC}")
        print(f"Expected format: https://github.com/username/repo.git")
        print(f"Current value: {repo_url}")

def check_git_config():
    """Check Git configuration"""
    print_banner("Checking Git Configuration")
    
    # Check if Git is installed
    git_version, success = run_command("git --version")
    if not success:
        print(f"{Colors.FAIL}❌ Git is not installed or not in PATH{Colors.ENDC}")
        return False
    
    print(f"{Colors.GREEN}✓ Git version: {git_version}{Colors.ENDC}")
    
    # Check Git configuration
    git_config, success = run_command("git config --list")
    if not success:
        print(f"{Colors.FAIL}❌ Failed to get Git configuration{Colors.ENDC}")
        return False
    
    # Extract user config
    user_name = None
    user_email = None
    for line in git_config.split('\n'):
        if line.startswith('user.name='):
            user_name = line.split('=', 1)[1]
        elif line.startswith('user.email='):
            user_email = line.split('=', 1)[1]
    
    if user_name:
        print(f"{Colors.GREEN}✓ Git user.name: {user_name}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ Git user.name not configured{Colors.ENDC}")
    
    if user_email:
        print(f"{Colors.GREEN}✓ Git user.email: {user_email}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ Git user.email not configured{Colors.ENDC}")
    
    return True

def test_git_connection():
    """Test connection to the Git remote repository"""
    print_banner("Testing Git Remote Connection")
    
    # Check if we're in a Git repository
    is_git_repo, success = run_command("git rev-parse --is-inside-work-tree")
    if not success or is_git_repo != "true":
        print(f"{Colors.WARNING}Not currently in a Git repository. Creating a temporary one for testing.{Colors.ENDC}")
        
        # Create a temporary directory for testing
        test_dir = tempfile.mkdtemp(prefix="git-test-")
        os.chdir(test_dir)
        print(f"Changed to temporary directory: {test_dir}")
        
        # Initialize Git repository
        init_result, success = run_command("git init")
        if not success:
            print(f"{Colors.FAIL}Failed to initialize Git repository.{Colors.ENDC}")
            return False
        
        # Set up Git user for this repository
        username = os.environ.get('GIT_USERNAME', 'AwaazTimetable App')
        email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        
        run_command(f'git config user.name "{username}"')
        run_command(f'git config user.email "{email}"')
    
    # Get remote URL from environment variable
    repo_url = os.environ.get('GIT_REPO_URL', '')
    if not repo_url:
        print(f"{Colors.FAIL}GIT_REPO_URL environment variable not set.{Colors.ENDC}")
        return False
    
    # Get credentials
    username = os.environ.get('GIT_USERNAME', '')
    token = os.environ.get('GIT_TOKEN', '')
    
    if not username or not token:
        print(f"{Colors.FAIL}GIT_USERNAME and/or GIT_TOKEN environment variables not set.{Colors.ENDC}")
        return False
    
    # Construct authenticated URL
    auth_url = repo_url
    if repo_url.startswith('https://'):
        auth_url = repo_url.replace('https://', f'https://{username}:{token}@')
    
    # Set up remote
    remotes, _ = run_command("git remote")
    if 'origin' not in remotes.split():
        print(f"{Colors.CYAN}Adding remote 'origin'...{Colors.ENDC}")
        run_command(f'git remote add origin "{auth_url}"')
    else:
        print(f"{Colors.CYAN}Updating remote 'origin' URL...{Colors.ENDC}")
        run_command(f'git remote set-url origin "{auth_url}"')
    
    # Test connection
    print(f"{Colors.CYAN}Fetching from remote repository...{Colors.ENDC}")
    fetch_result, success = run_command("git fetch origin")
    
    if success:
        print(f"{Colors.GREEN}✓ Successfully connected to remote repository.{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}❌ Failed to connect to remote repository.{Colors.ENDC}")
        return False

def create_test_file_and_commit():
    """Create a test file and commit it"""
    print_banner("Creating Test Commit")
    
    # Create a test file
    test_file = "git_debug_test.txt"
    with open(test_file, 'w') as f:
        f.write(f"Git debug test file\n")
        f.write(f"Created at: {datetime.now().isoformat()}\n")
        f.write(f"Running from: {os.getcwd()}\n")
    
    print(f"{Colors.GREEN}Created test file: {test_file}{Colors.ENDC}")
    
    # Add file to Git
    add_result, success = run_command(f"git add {test_file}")
    if not success:
        print(f"{Colors.FAIL}Failed to add file to Git.{Colors.ENDC}")
        return False
    
    # Commit the file
    commit_result, success = run_command('git commit -m "Test commit from debug script"')
    if not success:
        print(f"{Colors.FAIL}Failed to commit file.{Colors.ENDC}")
        return False
    
    print(f"{Colors.GREEN}Successfully created test commit.{Colors.ENDC}")
    
    # Try to push
    print(f"{Colors.CYAN}Attempting to push commit...{Colors.ENDC}")
    
    # Get current branch
    branch, _ = run_command("git branch --show-current")
    if not branch:
        branch = "main"
    
    push_result, success = run_command(f"git push origin {branch}")
    
    if success:
        print(f"{Colors.GREEN}✓ Successfully pushed test commit.{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ Failed to push test commit.{Colors.ENDC}")
        
        # Try force push if there's a non-fast-forward error
        if "non-fast-forward" in push_result or "rejected" in push_result:
            force_push = input("Would you like to try force push? (y/n): ")
            if force_push.lower() == 'y':
                force_result, force_success = run_command(f"git push -f origin {branch}")
                if force_success:
                    print(f"{Colors.GREEN}✓ Successfully force pushed test commit.{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Failed to force push test commit.{Colors.ENDC}")
    
    # Clean up
    run_command(f"git reset --soft HEAD~1")
    run_command(f"git restore --staged {test_file}")
    os.remove(test_file)
    print(f"{Colors.CYAN}Cleaned up test file and commit.{Colors.ENDC}")
    
    return success

def monitor_git_directory(interval=2, verbose=False):
    """Monitor .git directory for changes in real-time"""
    print_banner("Starting Git Directory Monitor")
    
    if not os.path.isdir(".git"):
        print(f"{Colors.WARNING}No .git directory found in current location.{Colors.ENDC}")
        return
    
    # Get initial state
    head_file = os.path.join(".git", "HEAD")
    index_file = os.path.join(".git", "index")
    refs_dir = os.path.join(".git", "refs")
    
    head_mtime = os.path.getmtime(head_file) if os.path.exists(head_file) else 0
    index_mtime = os.path.getmtime(index_file) if os.path.exists(index_file) else 0
    
    print(f"{Colors.CYAN}Monitoring Git directory for changes (Press Ctrl+C to stop)...{Colors.ENDC}")
    
    try:
        while True:
            # Check HEAD file (current branch/commit)
            if os.path.exists(head_file):
                new_head_mtime = os.path.getmtime(head_file)
                if new_head_mtime > head_mtime:
                    head_mtime = new_head_mtime
                    with open(head_file, 'r') as f:
                        head_content = f.read().strip()
                    
                    print(f"\n{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] HEAD changed: {head_content}{Colors.ENDC}")
                    
                    # Show current commit
                    run_command("git log -1 --oneline")
            
            # Check index file (staging area)
            if os.path.exists(index_file):
                new_index_mtime = os.path.getmtime(index_file)
                if new_index_mtime > index_mtime:
                    index_mtime = new_index_mtime
                    print(f"\n{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] Git index changed{Colors.ENDC}")
                    
                    # Show staged changes
                    if verbose:
                        run_command("git status -s")
            
            # Check for new commits in local branches
            for branch_file in Path(refs_dir).glob("heads/*"):
                if os.path.isfile(branch_file):
                    branch_name = os.path.basename(branch_file)
                    with open(branch_file, 'r') as f:
                        commit_hash = f.read().strip()
                    
                    print(f"\n{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] Branch '{branch_name}' points to: {commit_hash}{Colors.ENDC}")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Git directory monitoring stopped.{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Debug Git operations in real-time")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--test-push", action="store_true", help="Perform a test push operation")
    parser.add_argument("--monitor", action="store_true", help="Monitor .git directory for changes")
    args = parser.parse_args()
    
    print_banner("AwaazTimetable Git Operations Debugger")
    
    # Show system information
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check environment variables
    check_env_variables()
    
    # Check Git configuration
    check_git_config()
    
    # Test Git connection
    test_git_connection()
    
    # Create test commit and push if requested
    if args.test_push:
        create_test_file_and_commit()
    
    # Start monitoring in a separate thread if requested
    if args.monitor:
        monitor_thread = threading.Thread(
            target=monitor_git_directory,
            args=(2, args.verbose),
            daemon=True
        )
        monitor_thread.start()
        
        try:
            # Keep the main thread alive
            while monitor_thread.is_alive():
                monitor_thread.join(1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
    
    print_banner("Git Operations Debugging Complete")
    
    # Summary
    if args.test_push:
        print(f"{Colors.CYAN}Test push operation completed. Check the output above for results.{Colors.ENDC}")
    
    print(f"\n{Colors.GREEN}To fix Git authentication issues:{Colors.ENDC}")
    print("1. Ensure GIT_REPO_URL, GIT_USERNAME, and GIT_TOKEN environment variables are set")
    print("2. Verify the repository exists on GitHub")
    print("3. Make sure your Personal Access Token has the 'repo' scope")
    print("4. For Render.com, add these as environment variables in the dashboard")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 