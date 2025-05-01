#!/usr/bin/env python3
"""
fix_git_render.py - Script to fix Git issues on Render.com

This script addresses common Git issues on Render.com, including:
1. Detached HEAD state
2. Missing Git configuration
3. Authentication issues with GitHub
4. Branch tracking problems

Run this script on your Render instance to fix Git-related issues:
python fix_git_render.py

Environment variables required:
- GIT_REPO_URL: URL of the GitHub repository
- GIT_USERNAME: GitHub username
- GIT_TOKEN: GitHub personal access token
"""

import os
import sys
import subprocess
import logging
import traceback
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [RenderGitFix] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('RenderGitFix')

def log_banner(message):
    """Log a message with a prominent banner for visibility"""
    banner = "\n" + "=" * 70 + "\n" + " " + message.center(68) + " \n" + "=" * 70
    logger.info(banner)
    print(banner)

def run_command(command, description, cwd=None, check=True, retry=0, retry_delay=3):
    """Run a command with optional retries and logs the output"""
    logger.info(f"Running command: {command}")
    
    for attempt in range(retry + 1):
        if attempt > 0:
            logger.info(f"Retry {attempt}/{retry} after waiting {retry_delay} seconds")
            time.sleep(retry_delay)
            
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check,
                shell=True
            )
            logger.info(f"{description} successful")
            
            if result.stdout:
                logger.info(f"Command output: {result.stdout.strip()}")
                
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"{description} failed (attempt {attempt+1}): {e.returncode}")
            
            if e.stdout:
                logger.error(f"Command stdout: {e.stdout}")
                
            if e.stderr:
                logger.error(f"Command stderr: {e.stderr}")
                
            if attempt == retry:
                # Last attempt failed
                return False, e.stderr
        except Exception as e:
            logger.error(f"{description} failed with unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            
            if attempt == retry:
                return False, str(e)

def check_environment_variables():
    """Check if required environment variables are set"""
    log_banner("CHECKING ENVIRONMENT VARIABLES")
    
    required_vars = {
        'GIT_REPO_URL': 'URL of the GitHub repository',
        'GIT_USERNAME': 'GitHub username',
        'GIT_TOKEN': 'GitHub personal access token'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        
        if not value:
            missing_vars.append(var)
            logger.error(f"Missing {var}: {description}")
        else:
            # Mask sensitive values
            if var == 'GIT_TOKEN':
                masked = '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '********'
                logger.info(f"{var} is set: {masked}")
            elif var == 'GIT_REPO_URL':
                logger.info(f"{var} is set: {value}")
            else:
                logger.info(f"{var} is set: {value}")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def check_repository_status():
    """Check the current status of the Git repository"""
    log_banner("CHECKING REPOSITORY STATUS")
    
    # Get the application root directory - try Render path first, then fall back to current directory
    app_dir = os.environ.get('RENDER_PROJECT_DIR', '/opt/render/project/src')
    logger.info(f"Checking project directory: {app_dir}")
    
    # If the Render directory doesn't exist, use the current directory
    if not os.path.isdir(app_dir):
        app_dir = os.getcwd()
        logger.info(f"Using current directory instead: {app_dir}")
    
    os.chdir(app_dir)
    
    # Check if .git directory exists
    if not os.path.isdir('.git'):
        logger.error("No .git directory found - this is not a Git repository!")
        return False
    
    # Check Git version
    success, git_version = run_command(
        "git --version", 
        "Checking Git version"
    )
    
    if not success:
        logger.error("Git is not installed or not accessible")
        return False
    
    # Check Git configuration
    success, git_config = run_command(
        "git config --list",
        "Checking Git configuration"
    )
    
    if not success:
        logger.error("Failed to get Git configuration")
        return False
    
    # Check if user.name and user.email are configured
    has_username = 'user.name' in git_config
    has_email = 'user.email' in git_config
    
    if not (has_username and has_email):
        logger.warning("Git user is not fully configured")
    
    # Check current branch
    success, git_branch = run_command(
        "git rev-parse --abbrev-ref HEAD",
        "Checking current branch"
    )
    
    if not success:
        logger.error("Failed to get current branch")
        return False
    
    # Check if we're in detached HEAD state
    if git_branch.strip() == 'HEAD':
        logger.warning("Repository is in DETACHED HEAD state! This needs to be fixed.")
        return 'detached'
    else:
        logger.info(f"Repository is on branch: {git_branch.strip()}")
    
    # Check remotes
    success, git_remote = run_command(
        "git remote -v",
        "Checking Git remotes"
    )
    
    if not success or 'origin' not in git_remote:
        logger.warning("No 'origin' remote found")
        return 'no_remote'
    
    logger.info(f"Remote repositories: \n{git_remote}")
    
    # Check if there are uncommitted changes
    success, git_status = run_command(
        "git status --porcelain",
        "Checking for uncommitted changes"
    )
    
    if git_status.strip():
        logger.warning(f"There are uncommitted changes: \n{git_status}")
    else:
        logger.info("Working directory is clean")
    
    return 'ok'

def setup_git_user():
    """Set up Git user configuration"""
    log_banner("SETTING UP GIT USER")
    
    git_username = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
    git_email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
    
    logger.info(f"Setting Git user.name to: {git_username}")
    success, _ = run_command(
        f'git config --global user.name "{git_username}"',
        "Setting Git user.name"
    )
    
    if not success:
        logger.error("Failed to set Git user.name")
        return False
    
    logger.info(f"Setting Git user.email to: {git_email}")
    success, _ = run_command(
        f'git config --global user.email "{git_email}"',
        "Setting Git user.email"
    )
    
    if not success:
        logger.error("Failed to set Git user.email")
        return False
    
    logger.info("Git user configuration completed successfully")
    return True

def setup_git_credentials():
    """Set up Git credentials for authentication with GitHub"""
    log_banner("SETTING UP GIT CREDENTIALS")
    
    git_username = os.environ.get('GIT_USERNAME')
    git_token = os.environ.get('GIT_TOKEN')
    git_repo_url = os.environ.get('GIT_REPO_URL')
    
    if not (git_username and git_token and git_repo_url):
        logger.error("Missing required environment variables for Git credentials")
        return False
    
    # Extract hostname from repo URL (usually github.com)
    if 'github.com' in git_repo_url:
        host = 'github.com'
    else:
        if '://' in git_repo_url:
            host = git_repo_url.split('://')[1].split('/')[0]
        else:
            host = git_repo_url.split(':')[0]
    
    logger.info(f"Using host: {host}")
    
    # Set up credential.helper
    logger.info("Setting up Git credential helper")
    success, _ = run_command(
        "git config --global credential.helper store",
        "Setting credential helper"
    )
    
    if not success:
        logger.error("Failed to set credential helper")
        return False
    
    # Create Git credentials file
    cred_path = os.path.expanduser('~/.git-credentials')
    cred_line = f"https://{git_username}:{git_token}@{host}\n"
    
    logger.info(f"Saving credentials to {cred_path}")
    try:
        with open(cred_path, 'w') as f:
            f.write(cred_line)
        os.chmod(cred_path, 0o600)  # Secure permissions
    except Exception as e:
        logger.error(f"Failed to save Git credentials: {str(e)}")
        return False
    
    # Set up the remote with the correct URL
    success, _ = run_command(
        "git remote -v",
        "Checking remote configuration"
    )
    
    # Use authenticated URL for remote
    auth_url = f"https://{git_username}:{git_token}@{host}/{git_repo_url.split('/')[-2]}/{git_repo_url.split('/')[-1]}"
    
    # Set or update the origin remote
    if 'origin' not in _:
        logger.info("Adding 'origin' remote")
        success, _ = run_command(
            f'git remote add origin "{auth_url}"',
            "Adding origin remote"
        )
    else:
        logger.info("Updating 'origin' remote URL")
        success, _ = run_command(
            f'git remote set-url origin "{auth_url}"',
            "Updating origin remote"
        )
    
    if not success:
        logger.error("Failed to set up Git remote")
        return False
    
    # Test the connection
    logger.info("Testing connection to remote repository")
    success, _ = run_command(
        "git ls-remote --heads origin",
        "Testing remote connection",
        retry=2
    )
    
    if not success:
        logger.error("Failed to connect to remote repository")
        return False
    
    logger.info("Successfully connected to remote repository")
    return True

def fix_detached_head():
    """Fix detached HEAD state by creating a branch and checking it out"""
    log_banner("FIXING DETACHED HEAD STATE")
    
    # Get the current commit hash
    success, current_commit = run_command(
        "git rev-parse HEAD",
        "Getting current commit hash"
    )
    
    if not success:
        logger.error("Failed to get current commit hash")
        return False
    
    current_commit = current_commit.strip()
    logger.info(f"Current commit: {current_commit}")
    
    # Check for existing branches
    success, branches_output = run_command(
        "git branch",
        "Listing branches"
    )
    
    if not success:
        logger.error("Failed to list branches")
        return False
    
    # Parse branches and look for main/master
    branches = [b.strip(' *') for b in branches_output.split('\n') if b.strip()]
    target_branch = None
    
    for branch_name in ['main', 'master']:
        if branch_name in branches:
            target_branch = branch_name
            break
    
    if target_branch:
        # If we found main or master, check it out
        logger.info(f"Found existing branch: {target_branch}")
        success, _ = run_command(
            f"git checkout {target_branch}",
            f"Checking out {target_branch} branch"
        )
        
        if not success:
            logger.error(f"Failed to checkout {target_branch} branch")
            # Fall through to create a new branch
        else:
            # Reset the branch to current commit
            logger.info(f"Resetting {target_branch} to current commit: {current_commit}")
            success, _ = run_command(
                f"git reset --hard {current_commit}",
                f"Resetting {target_branch} to current commit"
            )
            
            if not success:
                logger.error(f"Failed to reset {target_branch} to current commit")
                return False
            
            logger.info(f"Successfully moved to branch {target_branch}")
            return True
    
    # If no main/master branch or checkout failed, create a new branch
    new_branch = "main"
    logger.info(f"Creating new branch: {new_branch}")
    success, _ = run_command(
        f"git checkout -b {new_branch}",
        f"Creating and checking out new branch: {new_branch}"
    )
    
    if not success:
        logger.error(f"Failed to create branch: {new_branch}")
        return False
    
    logger.info(f"Successfully created and checked out branch: {new_branch}")
    return True

def setup_branch_tracking():
    """Set up branch tracking with remote repository"""
    log_banner("SETTING UP BRANCH TRACKING")
    
    # Get current branch
    success, current_branch = run_command(
        "git rev-parse --abbrev-ref HEAD",
        "Getting current branch"
    )
    
    if not success:
        logger.error("Failed to get current branch")
        return False
    
    current_branch = current_branch.strip()
    logger.info(f"Current branch: {current_branch}")
    
    # Check if the branch exists on remote
    success, remote_refs = run_command(
        f"git ls-remote --heads origin {current_branch}",
        "Checking if remote branch exists",
        check=False  # Don't fail if it doesn't exist
    )
    
    remote_exists = current_branch in remote_refs
    
    if remote_exists:
        logger.info(f"Remote branch 'origin/{current_branch}' exists")
        
        # Set up tracking
        success, _ = run_command(
            f"git branch --set-upstream-to=origin/{current_branch} {current_branch}",
            "Setting up tracking with remote branch"
        )
        
        if not success:
            logger.error("Failed to set up branch tracking")
            return False
        
        # Pull changes from remote
        success, _ = run_command(
            f"git pull origin {current_branch} --allow-unrelated-histories",
            "Pulling changes from remote branch",
            check=False  # Don't fail if pull fails, we'll push anyway
        )
    else:
        logger.info(f"Remote branch 'origin/{current_branch}' does not exist, will create it on push")
    
    # Push the branch to remote
    success, push_output = run_command(
        f"git push -u origin {current_branch}",
        "Pushing branch to remote",
        retry=2
    )
    
    if not success:
        logger.error("Failed to push branch to remote")
        return False
    
    logger.info(f"Successfully set up tracking for branch {current_branch}")
    return True

def add_git_test_support():
    """Add 'git_test' to meta.json next_ids to prevent errors"""
    log_banner("ADDING GIT_TEST SUPPORT")
    
    # Check if data directory exists
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.isdir(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return False
    
    # Check if meta.json exists
    meta_file = os.path.join(data_dir, 'meta.json')
    if not os.path.isfile(meta_file):
        logger.error(f"Meta file not found: {meta_file}")
        return False
    
    # Read the meta.json file
    import json
    try:
        with open(meta_file, 'r') as f:
            meta_data = json.load(f)
        
        # Check if git_test is already in next_ids
        next_ids = meta_data.get('next_ids', {})
        if 'git_test' not in next_ids:
            logger.info("Adding 'git_test' to next_ids in meta.json")
            next_ids['git_test'] = 1
            meta_data['next_ids'] = next_ids
            
            # Write the updated meta.json
            with open(meta_file, 'w') as f:
                json.dump(meta_data, f, indent=2)
            
            logger.info("Successfully added 'git_test' to meta.json")
        else:
            logger.info("'git_test' already exists in meta.json")
        
        # Create git_test directory if needed
        git_test_dir = os.path.join(data_dir, 'git_test')
        if not os.path.isdir(git_test_dir):
            logger.info(f"Creating git_test directory: {git_test_dir}")
            os.makedirs(git_test_dir, exist_ok=True)
        
        # Commit the changes
        success, _ = run_command(
            "git add data/meta.json",
            "Adding meta.json to Git"
        )
        
        if not success:
            logger.error("Failed to add meta.json to Git")
            return False
        
        success, _ = run_command(
            'git commit -m "Add git_test to meta.json" --allow-empty',
            "Committing meta.json changes"
        )
        
        if not success:
            logger.error("Failed to commit meta.json changes")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error updating meta.json: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to fix Git issues on Render.com"""
    log_banner("RENDER GIT FIX UTILITY")
    logger.info("Starting script to fix Git issues on Render.com")
    
    # Check environment variables
    if not check_environment_variables():
        logger.error("Environment variable check failed")
        return 1
    
    # Check repository status
    repo_status = check_repository_status()
    if repo_status is False:
        logger.error("Repository status check failed")
        return 1
    
    # Set up Git user
    if not setup_git_user():
        logger.error("Git user setup failed")
        return 1
    
    # Set up Git credentials
    if not setup_git_credentials():
        logger.error("Git credentials setup failed")
        return 1
    
    # Fix detached HEAD if needed
    if repo_status == 'detached':
        if not fix_detached_head():
            logger.error("Failed to fix detached HEAD state")
            return 1
    
    # Set up branch tracking
    if not setup_branch_tracking():
        logger.error("Failed to set up branch tracking")
        return 1
    
    # Add git_test support to meta.json
    if not add_git_test_support():
        logger.warning("Failed to add git_test support to meta.json")
        # Not critical, continue
    
    log_banner("RENDER GIT FIX COMPLETED")
    logger.info("Successfully fixed Git issues on Render.com")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 