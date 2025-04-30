#!/usr/bin/env python3
"""
fix_git_push.py - Script to fix Git push issues on Render.com

This script addresses specific issues with Git push operations on Render.com,
particularly the "destination is not a full refname" error.

Usage:
    python fix_git_push.py

Environment variables required:
    GIT_REPO_URL: URL of the remote Git repository
    GIT_USERNAME: GitHub username for authentication
    GIT_TOKEN: GitHub personal access token for authentication
"""

import os
import sys
import subprocess
import time
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [GitFix] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitFix')

def log_banner(message):
    """Log a message with a prominent banner for visibility"""
    banner = "\n" + "=" * 70 + "\n" + " " + message.center(68) + " \n" + "=" * 70
    logger.info(banner)
    print(banner)

def verify_environment():
    """Verify that the necessary environment variables are set"""
    log_banner("CHECKING ENVIRONMENT")
    required_vars = ['GIT_REPO_URL', 'GIT_USERNAME', 'GIT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            logger.error(f"Missing environment variable: {var}")
        else:
            # Mask sensitive values in logs
            if var == 'GIT_TOKEN':
                masked_value = value[:4] + '****' + value[-4:] if len(value) > 8 else '********'
                logger.info(f"{var} is set: {masked_value}")
            elif var == 'GIT_REPO_URL':
                # Simplify URL logging for security
                if '@' in value:
                    parts = value.split('@')
                    masked_url = 'https://***:***@' + parts[1]
                else:
                    masked_url = value
                logger.info(f"{var} is set: {masked_url}")
            else:
                logger.info(f"{var} is set: {value}")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("All required environment variables are set")
    return True

def run_command(command, description, cwd=None, check=True):
    """Run a command and log the output"""
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        logger.info(f"{description} successful")
        logger.debug(f"Command output: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed: {e.returncode}")
        if e.stderr:
            logger.error(f"Error details: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"{description} failed with unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def setup_git_credentials():
    """Set up Git credentials for authentication"""
    log_banner("SETTING UP GIT CREDENTIALS")
    
    git_username = os.environ.get('GIT_USERNAME')
    git_token = os.environ.get('GIT_TOKEN')
    git_email = os.environ.get('GIT_EMAIL', f"{git_username}@users.noreply.github.com")
    
    # Set Git user configuration
    run_command(['git', 'config', 'user.name', git_username], "Setting Git username")
    run_command(['git', 'config', 'user.email', git_email], "Setting Git email")
    
    # Set credential helper
    run_command(['git', 'config', 'credential.helper', 'store'], "Setting credential helper")
    
    # Get repository URL and extract host
    git_repo_url = os.environ.get('GIT_REPO_URL')
    if 'github.com' in git_repo_url:
        host = 'github.com'
    else:
        if '://' in git_repo_url:
            host = git_repo_url.split('://')[1].split('/')[0]
        else:
            host = git_repo_url.split(':')[0]
    
    logger.info(f"Using host: {host}")
    
    # Create credentials file
    cred_path = os.path.expanduser('~/.git-credentials')
    with open(cred_path, 'w') as f:
        f.write(f"https://{git_username}:{git_token}@{host}\n")
    
    logger.info(f"Git credentials saved to {cred_path}")
    
    # Verify remote configurations
    success, output = run_command(['git', 'remote', '-v'], "Checking Git remotes")
    if success:
        if 'origin' not in output:
            logger.warning("No 'origin' remote found, adding it now")
            run_command(['git', 'remote', 'add', 'origin', git_repo_url], "Adding origin remote")
        else:
            logger.info("Updating origin remote URL")
            run_command(['git', 'remote', 'set-url', 'origin', git_repo_url], "Updating origin remote")
    
    return True

def test_git_connection():
    """Test connection to the remote repository"""
    log_banner("TESTING GIT CONNECTION")
    
    success, output = run_command(
        ['git', 'ls-remote', '--heads', 'origin'],
        "Testing connection to remote repository"
    )
    
    if success:
        logger.info("Successfully connected to remote repository")
        logger.info(f"Remote heads: {output}")
        return True
    else:
        logger.error("Failed to connect to remote repository")
        return False

def try_git_push_methods():
    """Try different methods for pushing to the remote repository"""
    log_banner("TRYING DIFFERENT PUSH METHODS")
    
    # Create a test file for commit
    test_file = 'git_push_fix_test.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(test_file, 'w') as f:
        f.write(f"Git push fix test\nCreated at: {timestamp}\n")
    
    # Add and commit the test file
    run_command(['git', 'add', test_file], "Adding test file to Git")
    run_command(
        ['git', 'commit', '-m', f"Test commit for push fix - {timestamp}"],
        "Committing test file"
    )
    
    # Get current branch
    success, branch_output = run_command(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        "Getting current branch"
    )
    
    if not success:
        logger.error("Failed to get current branch")
        return False
    
    current_branch = branch_output.strip()
    logger.info(f"Current branch: {current_branch}")
    
    # Try different push methods
    push_methods = [
        {
            "name": "Method 1: Standard push with refs/heads format",
            "command": ['git', 'push', 'origin', f"HEAD:refs/heads/{current_branch}"]
        },
        {
            "name": "Method 2: Standard push",
            "command": ['git', 'push', 'origin', 'HEAD']
        },
        {
            "name": "Method 3: Push to named branch",
            "command": ['git', 'push', 'origin', current_branch]
        },
        {
            "name": "Method 4: Simple push",
            "command": ['git', 'push']
        },
        {
            "name": "Method 5: Force push",
            "command": ['git', 'push', '-f', 'origin', current_branch]
        },
        {
            "name": "Method 6: Upstream tracking push",
            "command": ['git', 'push', '-u', 'origin', current_branch]
        }
    ]
    
    for method in push_methods:
        logger.info(f"Trying {method['name']}")
        success, output = run_command(
            method['command'],
            f"Pushing using {method['name']}",
            check=False  # Don't exit on error, try the next method
        )
        
        if success:
            log_banner(f"PUSH SUCCESSFUL: {method['name']}")
            logger.info(f"Successfully pushed using {method['name']}")
            return True
    
    log_banner("ALL PUSH METHODS FAILED")
    logger.error("All push methods failed")
    return False

def fix_git_config():
    """Fix Git configuration issues that might prevent pushing"""
    log_banner("FIXING GIT CONFIGURATION")
    
    # Ensure push.default is set to 'simple' or 'current'
    run_command(['git', 'config', 'push.default', 'current'], "Setting push.default")
    
    # Check if we need to allow force pushes
    run_command(['git', 'config', 'receive.denyNonFastForwards', 'false'], "Allowing non-fast-forward pushes")
    
    # Fix any issues with fetch settings
    run_command(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'], "Setting fetch configuration")
    
    return True

def main():
    """Main function to fix Git push issues"""
    log_banner("GIT PUSH FIX UTILITY")
    logger.info("Starting Git push fix utility")
    
    # Step 1: Verify environment variables
    if not verify_environment():
        logger.error("Environment check failed, cannot continue")
        return 1
    
    # Step 2: Set up Git credentials
    if not setup_git_credentials():
        logger.error("Failed to set up Git credentials")
        return 1
    
    # Step 3: Fix Git configuration
    if not fix_git_config():
        logger.error("Failed to fix Git configuration")
        return 1
    
    # Step 4: Test Git connection
    if not test_git_connection():
        logger.error("Failed to connect to remote repository")
        return 1
    
    # Step 5: Try different push methods
    if try_git_push_methods():
        log_banner("GIT PUSH FIX SUCCESSFUL")
        logger.info("Successfully fixed Git push issues")
        return 0
    else:
        log_banner("GIT PUSH FIX FAILED")
        logger.error("Failed to fix Git push issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 