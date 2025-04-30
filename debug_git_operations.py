#!/usr/bin/env python3
"""
Debug script for testing Git operations on Render.com.
This script performs various Git operations with detailed logging to
diagnose issues with Git pushing to remote repositories.

Usage:
    python debug_git_operations.py [--create-test-file] [--full-diagnostic]

Options:
    --create-test-file  Create a test file and commit/push it
    --full-diagnostic   Run a full diagnostic of the Git setup

Example:
    python debug_git_operations.py --create-test-file --full-diagnostic
"""

import os
import subprocess
import sys
import argparse
import time
from datetime import datetime

# Try import from app directory
try:
    from app.git_utils import commit_and_push, run_git_diagnostic
except ImportError:
    # If running from app directory
    try:
        from git_utils import commit_and_push, run_git_diagnostic
    except ImportError:
        print("Error: Could not import git_utils. Make sure you're running this from the project root or app directory.")
        sys.exit(1)

def print_banner(message):
    """Print a formatted banner message"""
    banner = "\n" + "=" * 80 + "\n" + " " + message.center(78) + " \n" + "=" * 80
    print(banner)

def run_command(cmd, exit_on_error=False):
    """Run a command with detailed output"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        print(f"Error running '{cmd}':")
        print(f"Exit code: {e.returncode}")
        if e.stderr:
            print(f"Error output:\n{e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return e.stderr.strip() if e.stderr else "", False

def check_env_variables():
    """Check if required environment variables are set"""
    print_banner("CHECKING ENVIRONMENT VARIABLES")
    
    required_vars = ['GIT_REPO_URL', 'GIT_USERNAME', 'GIT_TOKEN']
    all_present = True
    
    for var in required_vars:
        value = os.environ.get(var, 'Not set')
        
        # Mask token for security
        if var == 'GIT_TOKEN' and value != 'Not set':
            display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '****'
            print(f"{var}: {display_value}")
        elif var == 'GIT_REPO_URL' and value != 'Not set':
            # Mask any credentials in URL
            if '@' in value:
                parts = value.split('@')
                display_value = 'https://***:***@' + parts[1]
                print(f"{var}: {display_value}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: {value}")
        
        if value == 'Not set':
            all_present = False
    
    return all_present

def check_git_config():
    """Check Git configuration"""
    print_banner("CHECKING GIT CONFIGURATION")
    
    run_command("git config --list")
    
    user_name, success1 = run_command("git config user.name")
    user_email, success2 = run_command("git config user.email")
    
    if not success1 or not user_name:
        print("Git user name is not configured!")
        # Set default user name from environment or default
        user_name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
        run_command(f'git config user.name "{user_name}"')
        print(f"Git user name set to: {user_name}")
    
    if not success2 or not user_email:
        print("Git user email is not configured!")
        # Set default user email
        user_email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        run_command(f'git config user.email "{user_email}"')
        print(f"Git user email set to: {user_email}")
    
    return True

def test_git_connection():
    """Test Git connection to remote"""
    print_banner("TESTING GIT CONNECTION")
    
    remote_url, success = run_command("git config --get remote.origin.url")
    if not success or not remote_url:
        print("No Git remote URL configured!")
        
        # Get repo URL from environment
        repo_url = os.environ.get('GIT_REPO_URL')
        if not repo_url:
            print("ERROR: GIT_REPO_URL environment variable not set!")
            return False
        
        # Add 'origin' remote
        print(f"Adding remote 'origin' with URL: {repo_url}")
        run_command(f'git remote add origin "{repo_url}"')
    else:
        print(f"Remote URL: {remote_url}")
    
    # Update remote URL with authentication if needed
    if 'GIT_USERNAME' in os.environ and 'GIT_TOKEN' in os.environ:
        username = os.environ.get('GIT_USERNAME')
        token = os.environ.get('GIT_TOKEN')
        
        remote_url, _ = run_command("git config --get remote.origin.url")
        
        # Only update if it's a HTTPS URL without credentials
        if remote_url.startswith('https://') and '@' not in remote_url:
            print("Updating remote URL with authentication...")
            auth_url = remote_url.replace('https://', f'https://{username}:{token}@')
            run_command(f'git remote set-url origin "{auth_url}"')
            print("Remote URL updated with authentication credentials")
    
    # Test connection
    output, success = run_command("git ls-remote origin HEAD")
    
    if success:
        print("✅ Successfully connected to remote repository!")
        return True
    else:
        print("❌ Failed to connect to remote repository!")
        
        if "Repository not found" in output:
            print("ERROR: Repository not found. Make sure it exists and you have access to it.")
        elif "Authentication failed" in output:
            print("ERROR: Authentication failed. Check your username and token.")
        
        return False

def create_test_file_and_commit():
    """Create a test file and commit it"""
    print_banner("CREATING TEST FILE AND COMMITTING")
    
    # Create a test file
    test_file = 'git_debug_test.txt'
    with open(test_file, 'w') as f:
        f.write(f"Git debug test file\n")
        f.write(f"Created at: {datetime.now().isoformat()}\n")
        f.write(f"Environment: Render.com\n")
    
    print(f"Created test file: {test_file}")
    
    # Check if our app's commit_and_push function works
    print("\nUsing app's commit_and_push function:")
    success = commit_and_push("Debug test commit")
    
    if success:
        print("✅ App's commit_and_push function reported success")
    else:
        print("❌ App's commit_and_push function reported failure")
    
    # Try manual commit and push
    print("\nTrying manual commit and push:")
    run_command("git add git_debug_test.txt")
    run_command("git commit -m \"Debug test commit - created via debug script\"")
    output, success = run_command("git push origin HEAD")
    
    if success:
        print("✅ Successfully pushed to remote repository!")
    else:
        print("❌ Failed to push to remote repository")
        print(f"Error: {output}")
    
    # Cleanup
    os.remove(test_file)
    return success

def main():
    parser = argparse.ArgumentParser(description='Debug Git operations on Render.com')
    parser.add_argument('--create-test-file', action='store_true', help='Create a test file and commit/push it')
    parser.add_argument('--full-diagnostic', action='store_true', help='Run a full diagnostic of the Git setup')
    
    args = parser.parse_args()
    
    print_banner("GIT OPERATIONS DEBUGGING TOOL")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Check environment variables
    env_ok = check_env_variables()
    if not env_ok:
        print("WARNING: Some required environment variables are not set!")
    
    # Check Git configuration
    git_config_ok = check_git_config()
    
    # Test Git connection
    connection_ok = test_git_connection()
    
    # Run full diagnostic if requested
    if args.full_diagnostic:
        try:
            print("\nRunning full Git diagnostic...")
            run_git_diagnostic()
        except Exception as e:
            print(f"Error running Git diagnostic: {str(e)}")
    
    # Create test file and commit if requested
    if args.create_test_file:
        create_test_file_and_commit()
    
    # Summary
    print_banner("DEBUGGING SUMMARY")
    print(f"Environment Variables: {'✅ OK' if env_ok else '❌ Missing some variables'}")
    print(f"Git Configuration: {'✅ OK' if git_config_ok else '❌ Issues detected'}")
    print(f"Git Connection: {'✅ OK' if connection_ok else '❌ Connection failed'}")
    
    if args.create_test_file:
        print("Test File: Created and attempted to commit/push")
    
    print("\nFor detailed logs, check the application logs on Render.com")

if __name__ == "__main__":
    main() 