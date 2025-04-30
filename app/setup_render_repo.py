#!/usr/bin/env python3
"""
Script to set up a local Git repository on Render.com for file persistence
if the normal Git clone process didn't create proper Git metadata.
"""

import os
import subprocess
import sys

def run_command(cmd, exit_on_error=False):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running '{cmd}': {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return None

def setup_local_repo():
    """Set up a local Git repository if needed"""
    print("Checking for Git repository...")
    
    # Get the application root directory
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(app_dir)
    
    # Check if .git directory exists and is properly set up
    if not os.path.isdir('.git'):
        print("No .git directory found. Setting up local Git repository...")
        
        # Initialize a new repository
        run_command("git init", exit_on_error=True)
        print("Git repository initialized.")
        
        # Create a .gitignore file
        if not os.path.exists('.gitignore'):
            with open('.gitignore', 'w') as f:
                f.write("# Python bytecode\n__pycache__/\n*.py[cod]\n*$py.class\n\n")
                f.write("# Virtual environment\nvenv/\nenv/\nENV/\n\n")
                f.write("# Local data that shouldn't be in git\n*.db\ninstance/\n\n")
                f.write("# Logs\n*.log\n")
        
        # Set up Git user
        email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
        run_command(f'git config user.email "{email}"')
        run_command(f'git config user.name "{name}"')
        
        # Add and commit files
        run_command("git add .")
        run_command('git commit -m "Initial commit for local persistence"')
        
        print("Local Git repository set up successfully.")
    else:
        print(".git directory exists.")
        
        # Check if the user and email are configured
        email = run_command("git config user.email")
        name = run_command("git config user.name")
        
        if not email or not name:
            print("Git user not configured. Setting up Git user...")
            email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
            name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
            run_command(f'git config user.email "{email}"')
            run_command(f'git config user.name "{name}"')
            print("Git user configured.")
    
    # Make sure the data directory exists and is tracked
    data_dir = os.path.join(app_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    for subdir in ['caregivers', 'templates', 'calendars', 'shifts', 'checklists', 'activities', 'activity_categories']:
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
    
    # Make sure meta.json exists
    meta_file = os.path.join(data_dir, 'meta.json')
    if not os.path.exists(meta_file):
        with open(meta_file, 'w') as f:
            f.write('{\n  "next_ids": {\n    "caregiver": 1,\n    "template": 1,\n    "calendar": 1,\n')
            f.write('    "shift": 1,\n    "checklist_item": 1,\n    "activity": 1,\n    "activity_category": 1\n  }\n}')
    
    # Add all data files to Git
    run_command("git add data/")
    
    # Commit if there are changes
    status = run_command("git status --porcelain")
    if status:
        run_command('git commit -m "Update data files"')
        print("Committed data directory changes.")
    
    print("Git setup completed successfully.")

if __name__ == "__main__":
    setup_local_repo() 