#!/usr/bin/env python3
"""
fix_detached_head.py - Script to fix detached HEAD issues in the Git repository

This script:
1. Checks if the repository is in a detached HEAD state
2. Creates a new branch or moves to an existing branch
3. Ensures that all commits are properly connected to a branch
4. Sets up proper tracking with the remote repository

Run this script from the project root directory:
    python fix_detached_head.py
"""

import os
import sys
import subprocess
import logging
import traceback
from datetime import datetime

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

def run_command(command, description, cwd=None, check=True):
    """Run a command and log the output"""
    logger.info(f"Running command: {command}")
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

def verify_git_state():
    """Verify the current state of the Git repository"""
    log_banner("CHECKING GIT REPOSITORY STATE")
    
    # Check Git version
    success, git_version = run_command(
        "git --version",
        "Checking Git version"
    )
    
    if not success:
        logger.error("Git is not installed or not accessible")
        return False
    
    logger.info(f"Git version: {git_version}")
    
    # Check if .git directory exists
    if not os.path.isdir('.git'):
        logger.error("No .git directory found. Git operations will fail!")
        return False
    
    # Get current HEAD reference
    success, head_ref = run_command(
        "git symbolic-ref -q HEAD || echo 'DETACHED'",
        "Checking HEAD reference"
    )
    
    if not success:
        logger.error("Failed to check HEAD reference")
        return False
    
    if head_ref.strip() == 'DETACHED':
        logger.warning("Repository is in detached HEAD state!")
        return 'detached'
    else:
        logger.info(f"Repository is on a branch: {head_ref}")
        return 'on_branch'

def fix_detached_head():
    """Fix the detached HEAD state by creating a branch and moving to it"""
    log_banner("FIXING DETACHED HEAD STATE")
    
    # First, check if there are any local changes
    success, status_output = run_command(
        "git status --porcelain",
        "Checking for uncommitted changes"
    )
    
    if status_output.strip():
        logger.warning("There are uncommitted changes. Committing them first.")
        run_command(
            "git add -A",
            "Adding all changes to index"
        )
        run_command(
            f"git commit -m 'Auto-commit before fixing detached HEAD - {datetime.now().isoformat()}'",
            "Committing changes"
        )
    
    # Get the current commit hash
    success, current_commit = run_command(
        "git rev-parse HEAD",
        "Getting current commit hash"
    )
    
    if not success:
        logger.error("Failed to get current commit hash")
        return False
    
    logger.info(f"Current commit: {current_commit}")
    
    # Check for existing branches
    success, branch_output = run_command(
        "git branch",
        "Listing branches"
    )
    
    branch_list = [b.strip() for b in branch_output.split('\n') if b.strip()]
    main_branch = None
    
    # Look for main or master branch
    for branch in branch_list:
        clean_name = branch.replace('*', '').strip()
        if clean_name in ['main', 'master']:
            main_branch = clean_name
            break
    
    # If main branch exists, checkout that branch
    if main_branch:
        logger.info(f"Found {main_branch} branch, checking it out")
        success, _ = run_command(
            f"git checkout {main_branch}",
            f"Checking out {main_branch} branch"
        )
        
        if not success:
            logger.error(f"Failed to checkout {main_branch} branch")
            # Continue with plan B
        else:
            # Make sure the branch is updated with the detached HEAD commit
            logger.info(f"Resetting {main_branch} branch to current commit")
            run_command(
                f"git reset --hard {current_commit}",
                f"Resetting {main_branch} branch to current commit"
            )
            return True
    
    # If no main branch or checkout failed, create a new branch
    branch_name = "main"
    logger.info(f"Creating new branch '{branch_name}' at the current commit")
    
    success, _ = run_command(
        f"git checkout -b {branch_name}",
        f"Creating and checking out new branch '{branch_name}'"
    )
    
    if not success:
        logger.error(f"Failed to create new branch '{branch_name}'")
        return False
    
    logger.info(f"Successfully created and checked out branch '{branch_name}'")
    return True

def setup_remote_tracking():
    """Setup proper remote tracking for the current branch"""
    log_banner("SETTING UP REMOTE TRACKING")
    
    # Get current branch
    success, branch_output = run_command(
        "git rev-parse --abbrev-ref HEAD",
        "Getting current branch"
    )
    
    if not success:
        logger.error("Failed to get current branch")
        return False
    
    current_branch = branch_output.strip()
    logger.info(f"Current branch: {current_branch}")
    
    # Check remotes
    success, remote_output = run_command(
        "git remote -v",
        "Checking remotes"
    )
    
    if 'origin' not in remote_output:
        logger.error("No 'origin' remote found")
        
        # Check for GIT_REPO_URL
        git_repo_url = os.environ.get('GIT_REPO_URL')
        if not git_repo_url:
            logger.error("GIT_REPO_URL environment variable not set")
            return False
        
        logger.info(f"Adding 'origin' remote with URL: {git_repo_url}")
        success, _ = run_command(
            f"git remote add origin {git_repo_url}",
            "Adding 'origin' remote"
        )
        
        if not success:
            logger.error("Failed to add 'origin' remote")
            return False
    
    # Check if remote branch exists
    success, ls_remote_output = run_command(
        f"git ls-remote --heads origin {current_branch}",
        "Checking if remote branch exists",
        check=False  # Don't fail if it doesn't exist
    )
    
    if not success or current_branch not in ls_remote_output:
        logger.info(f"Remote branch 'origin/{current_branch}' doesn't exist yet")
        logger.info("Will try to push and create it")
        
        # Try to push (this will fail if authentication is required)
        success, push_output = run_command(
            f"git push -u origin {current_branch}",
            f"Pushing and setting upstream for branch '{current_branch}'",
            check=False
        )
        
        if not success:
            logger.warning("Failed to push to remote. May need authentication.")
            
            # Try with credentials if available
            git_username = os.environ.get('GIT_USERNAME')
            git_token = os.environ.get('GIT_TOKEN')
            
            if git_username and git_token:
                logger.info("Credentials found, retrying with authentication")
                
                # Get the remote URL
                success, remote_url = run_command(
                    "git config --get remote.origin.url",
                    "Getting remote URL"
                )
                
                if not success:
                    logger.error("Failed to get remote URL")
                    return False
                
                # Add credentials to the URL
                if remote_url.startswith('https://'):
                    auth_url = remote_url.replace('https://', f'https://{git_username}:{git_token}@')
                    
                    # Update the remote URL with credentials
                    success, _ = run_command(
                        f"git remote set-url origin {auth_url}",
                        "Updating remote URL with credentials"
                    )
                    
                    if not success:
                        logger.error("Failed to update remote URL with credentials")
                        return False
                    
                    # Try pushing again
                    success, push_output = run_command(
                        f"git push -u origin {current_branch}",
                        f"Pushing and setting upstream for branch '{current_branch}' with credentials",
                        check=False
                    )
                    
                    if not success:
                        logger.error("Failed to push to remote even with credentials")
                        logger.error("Will continue with local branch only")
                    else:
                        logger.info(f"Successfully pushed and set upstream for branch '{current_branch}'")
                else:
                    logger.warning("Remote URL doesn't start with 'https://', can't add credentials")
                    logger.warning("Will continue with local branch only")
            else:
                logger.warning("No credentials found (GIT_USERNAME and GIT_TOKEN)")
                logger.warning("Will continue with local branch only")
        else:
            logger.info(f"Successfully pushed and set upstream for branch '{current_branch}'")
    else:
        logger.info(f"Remote branch 'origin/{current_branch}' exists")
        
        # Set upstream tracking
        success, _ = run_command(
            f"git branch --set-upstream-to=origin/{current_branch} {current_branch}",
            f"Setting upstream for branch '{current_branch}'"
        )
        
        if not success:
            logger.error(f"Failed to set upstream for branch '{current_branch}'")
            return False
        
        logger.info(f"Successfully set upstream for branch '{current_branch}'")
    
    return True

def main():
    """Main function to fix detached HEAD and setup proper tracking"""
    log_banner("GIT REPOSITORY FIX UTILITY")
    
    # Change to project root directory if needed
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    logger.info(f"Working in directory: {project_root}")
    
    # Check the current state of the repository
    git_state = verify_git_state()
    
    if git_state is False:
        logger.error("Failed to verify Git repository state")
        return 1
    
    # Fix detached HEAD if needed
    if git_state == 'detached':
        if not fix_detached_head():
            logger.error("Failed to fix detached HEAD state")
            return 1
        
        logger.info("Successfully fixed detached HEAD state")
    else:
        logger.info("Repository is already on a branch, no need to fix detached HEAD")
    
    # Setup remote tracking
    if not setup_remote_tracking():
        logger.error("Failed to setup remote tracking")
        return 1
    
    log_banner("GIT REPOSITORY FIX COMPLETED")
    logger.info("Git repository is now in a proper state")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 