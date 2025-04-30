#!/usr/bin/env python3
"""
Script to set up a local Git repository on Render.com for file persistence
if the normal Git clone process didn't create proper Git metadata.
"""

import os
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [GitDB Setup] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitDB_Setup')

def run_command(cmd, exit_on_error=False):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running '{cmd}': {e.stderr}")
        print(f"Error running '{cmd}': {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return None

def run_git_diagnostic():
    """Run comprehensive diagnostics on the Git repository"""
    logger.info("=============== GIT REPOSITORY DIAGNOSTICS ===============")
    
    # Get the application root directory
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(app_dir)
    logger.info(f"Working directory: {app_dir}")
    
    # Check Git version
    git_version = run_command("git --version")
    logger.info(f"Git version: {git_version}")
    
    # Check if .git directory exists
    git_dir_exists = os.path.isdir('.git')
    logger.info(f".git directory exists: {git_dir_exists}")
    
    if not git_dir_exists:
        logger.error("No .git directory found. Git operations will fail!")
        return False
    
    # Check Git configuration
    git_user = run_command("git config user.name")
    git_email = run_command("git config user.email")
    logger.info(f"Git user configured: {git_user} <{git_email}>")
    
    # Check remotes
    git_remotes = run_command("git remote -v")
    if git_remotes:
        logger.info(f"Git remotes:\n{git_remotes}")
    else:
        logger.warning("No Git remotes configured. Push operations will fail!")
    
    # Check current branch
    git_branch = run_command("git branch --show-current")
    logger.info(f"Current Git branch: {git_branch}")
    
    # Check latest commit
    git_latest_commit = run_command("git log -1 --oneline")
    if git_latest_commit:
        logger.info(f"Latest Git commit: {git_latest_commit}")
    else:
        logger.warning("No Git commits found. Repository may not be properly initialized.")
    
    # Check status (any uncommitted changes)
    git_status = run_command("git status --short")
    if git_status:
        logger.info(f"Uncommitted changes found:\n{git_status}")
    else:
        logger.info("No uncommitted changes")
    
    # Check if data directory is being tracked
    data_dir = os.path.join(app_dir, 'data')
    if os.path.exists(data_dir):
        data_tracked = run_command(f"git ls-files {data_dir}")
        if data_tracked:
            logger.info(f"Data directory is tracked with {len(data_tracked.split(os.linesep))} files")
        else:
            logger.warning("Data directory exists but is not tracked by Git!")
    else:
        logger.error("Data directory does not exist!")
    
    logger.info("=============== END DIAGNOSTICS ===============")
    return True

def setup_local_repo():
    """Set up a local Git repository if needed"""
    logger.info("Checking for Git repository...")
    
    # Get the application root directory
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(app_dir)
    
    # Check if .git directory exists and is properly set up
    if not os.path.isdir('.git'):
        logger.warning("No .git directory found. Setting up local Git repository...")
        
        # Initialize a new repository
        run_command("git init", exit_on_error=True)
        logger.info("Git repository initialized.")
        
        # Create a .gitignore file
        if not os.path.exists('.gitignore'):
            logger.info("Creating .gitignore file")
            with open('.gitignore', 'w') as f:
                f.write("# Python bytecode\n__pycache__/\n*.py[cod]\n*$py.class\n\n")
                f.write("# Virtual environment\nvenv/\nenv/\nENV/\n\n")
                f.write("# Local data that shouldn't be in git\n*.db\ninstance/\n\n")
                f.write("# Logs\n*.log\n")
        
        # Set up Git user
        email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
        logger.info(f"Setting Git user: {name} <{email}>")
        run_command(f'git config user.email "{email}"')
        run_command(f'git config user.name "{name}"')
        
        # Add and commit files
        logger.info("Adding and committing initial files")
        run_command("git add .")
        run_command('git commit -m "Initial commit for local persistence"')
        
        logger.info("Local Git repository set up successfully.")
    else:
        logger.info(".git directory exists.")
        
        # Check if the user and email are configured
        email = run_command("git config user.email")
        name = run_command("git config user.name")
        
        if not email or not name:
            logger.warning("Git user not configured. Setting up Git user...")
            email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
            name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
            run_command(f'git config user.email "{email}"')
            run_command(f'git config user.name "{name}"')
            logger.info("Git user configured.")
    
    # Make sure the data directory exists and is tracked
    data_dir = os.path.join(app_dir, 'data')
    if not os.path.exists(data_dir):
        logger.info("Creating data directory structure")
        os.makedirs(data_dir, exist_ok=True)
        
    for subdir in ['caregivers', 'templates', 'calendars', 'shifts', 'checklists', 'activities', 'activity_categories']:
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.exists(subdir_path):
            logger.info(f"Creating subdirectory: {subdir}")
            os.makedirs(subdir_path, exist_ok=True)
    
    # Make sure meta.json exists
    meta_file = os.path.join(data_dir, 'meta.json')
    if not os.path.exists(meta_file):
        logger.info("Creating meta.json file")
        with open(meta_file, 'w') as f:
            f.write('{\n  "next_ids": {\n    "caregiver": 1,\n    "template": 1,\n    "calendar": 1,\n')
            f.write('    "shift": 1,\n    "checklist_item": 1,\n    "activity": 1,\n    "activity_category": 1\n  }\n}')
    
    # Add all data files to Git
    logger.info("Adding data directory to Git")
    run_command("git add data/")
    
    # Commit if there are changes
    status = run_command("git status --porcelain")
    if status:
        logger.info("Committing data directory changes")
        run_command('git commit -m "Update data files"')
    
    # Run diagnostics
    run_git_diagnostic()
    
    logger.info("Git setup completed successfully.")
    return True

if __name__ == "__main__":
    setup_local_repo() 