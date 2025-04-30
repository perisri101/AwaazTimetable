#!/usr/bin/env python3
"""
Git Health Check and Auto-fix Script for AwaazTimetable

This script performs a comprehensive health check on the Git-based persistence system
and automatically fixes common issues. It verifies:

1. Git installation and configuration
2. Local repository setup and structure
3. Environment variables for authentication
4. Remote repository connection
5. Push capability

Usage: python git_health_check.py [--fix] [--verbose]

Options:
    --fix       Automatically fix issues when possible
    --verbose   Show detailed output
"""

import os
import sys
import subprocess
import argparse
import time
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import getpass
from pathlib import Path

# Constants
DATA_DIR = "data"
REQUIRED_ENV_VARS = ["GIT_REPO_URL", "GIT_USERNAME", "GIT_TOKEN"]

def print_banner(message, char='='):
    """Print a formatted banner message"""
    width = 80
    print(f"\n{char * width}")
    print(f" {message} ".center(width - 2).center(width, char))
    print(f"{char * width}\n")

def print_status(message, status, details=None):
    """Print a status message with color coding"""
    status_text = "✓ PASS" if status else "✗ FAIL"
    status_color = "\033[92m" if status else "\033[91m"  # Green for pass, red for fail
    reset_color = "\033[0m"
    
    print(f"{message.ljust(60)} {status_color}{status_text}{reset_color}")
    
    if details and not status:
        # Print error details indented
        for line in details.split('\n'):
            print(f"  → {line}")

def run_command(cmd, exit_on_error=False, show_output=False, capture_output=True):
    """Run a command and return its output and success status"""
    if show_output:
        print(f"Running: {cmd}")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            if show_output and result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return result.stdout.strip(), True
        else:
            # Just run the command without capturing output (prints directly)
            subprocess.run(cmd, shell=True, check=True)
            return "", True
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"Error: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
        if exit_on_error:
            sys.exit(1)
        return e.stderr.strip() if e.stderr else "", False

def check_git_installation():
    """Check if Git is installed and configured"""
    git_version, success = run_command("git --version")
    
    if not success:
        print_status("Git installation", False, "Git is not installed or not in PATH.")
        return False
    
    print_status("Git installation", True, f"Git version: {git_version}")
    return True

def check_git_configuration():
    """Check if Git user is configured"""
    git_config, success = run_command("git config --list")
    
    if not success:
        print_status("Git configuration", False, "Failed to get Git configuration.")
        return False
    
    # Check for user.name and user.email
    has_user_name = "user.name=" in git_config
    has_user_email = "user.email=" in git_config
    
    if not has_user_name or not has_user_email:
        missing = []
        if not has_user_name:
            missing.append("user.name")
        if not has_user_email:
            missing.append("user.email")
        
        print_status("Git configuration", False, f"Missing configuration: {', '.join(missing)}")
        return False
    
    print_status("Git configuration", True)
    return True

def fix_git_configuration(username=None, email=None):
    """Fix Git user configuration"""
    print_banner("Fixing Git Configuration", "-")
    
    if username is None:
        username = input("Enter Git username: ").strip() or "AwaazTimetable App"
    
    if email is None:
        email = input("Enter Git email: ").strip() or "app@awaaz-timetable.com"
    
    run_command(f'git config --global user.name "{username}"', show_output=True)
    run_command(f'git config --global user.email "{email}"', show_output=True)
    
    print("Git configuration updated.")
    return True

def check_local_repo():
    """Check if a local Git repository exists and is properly set up"""
    # Check if .git directory exists
    git_dir_exists = os.path.isdir(".git")
    
    if not git_dir_exists:
        print_status("Local Git repository", False, "No .git directory found.")
        return False
    
    # Check if it's a valid repo
    valid_repo, success = run_command("git rev-parse --is-inside-work-tree")
    
    if not success or valid_repo != "true":
        print_status("Local Git repository", False, "Not a valid Git repository.")
        return False
    
    # Check if data directory exists
    data_dir_exists = os.path.isdir(DATA_DIR)
    
    if not data_dir_exists:
        print_status("Data directory", False, f"'{DATA_DIR}' directory not found.")
        return False
    
    # Check if data directory is tracked
    is_tracked, success = run_command(f"git ls-files {DATA_DIR}/meta.json")
    
    if not success or not is_tracked:
        print_status("Data directory tracking", False, f"'{DATA_DIR}' directory is not tracked by Git.")
        return False
    
    print_status("Local Git repository", True)
    print_status("Data directory", True)
    print_status("Data directory tracking", True)
    return True

def setup_local_repo():
    """Set up a local Git repository"""
    print_banner("Setting up Local Git Repository", "-")
    
    # Initialize repository if needed
    if not os.path.isdir(".git"):
        run_command("git init", show_output=True)
    
    # Create data directory if needed
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"Created '{DATA_DIR}' directory.")
    
    # Create meta.json if it doesn't exist
    meta_file = os.path.join(DATA_DIR, "meta.json")
    if not os.path.exists(meta_file):
        initial_meta = {
            "next_ids": {
                "caregiver": 1,
                "template": 1,
                "calendar": 1,
                "shift": 1,
                "checklist_item": 1,
                "activity": 1,
                "activity_category": 1
            }
        }
        
        with open(meta_file, 'w') as f:
            json.dump(initial_meta, f, indent=2)
        
        print(f"Created initial '{meta_file}'.")
    
    # Create subdirectories
    subdirs = ['caregivers', 'templates', 'calendars', 'shifts', 'checklists', 
               'activities', 'activity_categories']
    
    for subdir in subdirs:
        os.makedirs(os.path.join(DATA_DIR, subdir), exist_ok=True)
    
    print(f"Created data subdirectories.")
    
    # Add data directory to Git
    run_command(f"git add {DATA_DIR}", show_output=True)
    
    # Make initial commit if there's no commit history
    has_commits, _ = run_command("git log -1")
    if not has_commits:
        run_command('git commit -m "Initial commit with data directory structure"', show_output=True)
        print("Made initial commit.")
    
    return True

def check_env_variables():
    """Check if required environment variables are set"""
    missing_vars = []
    
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print_status("Environment variables", False, f"Missing variables: {', '.join(missing_vars)}")
        return False
    
    # Make sure the repo URL is valid
    repo_url = os.environ.get('GIT_REPO_URL', '')
    if not repo_url.startswith('https://github.com/'):
        print_status("GIT_REPO_URL format", False, f"Invalid format: {repo_url}")
        return False
    
    print_status("Environment variables", True)
    return True

def set_env_variables():
    """Set environment variables for Git authentication"""
    print_banner("Setting Environment Variables", "-")
    
    # Get repo URL
    repo_url = os.environ.get('GIT_REPO_URL', '')
    if not repo_url or not repo_url.startswith('https://github.com/'):
        repo_url = input("Enter GitHub repository URL (https://github.com/username/repo.git): ").strip()
    
    # Get username
    username = os.environ.get('GIT_USERNAME', '')
    if not username:
        username = input("Enter GitHub username: ").strip()
    
    # Get token
    token = os.environ.get('GIT_TOKEN', '')
    if not token:
        token = getpass.getpass("Enter GitHub Personal Access Token (hidden input): ").strip()
    
    # Set environment variables for this session
    os.environ['GIT_REPO_URL'] = repo_url
    os.environ['GIT_USERNAME'] = username
    os.environ['GIT_TOKEN'] = token
    
    # Instructions for permanently setting these variables
    print("\nEnvironment variables set for this session.")
    print("\nTo set these permanently:")
    print("1. For Linux/Mac: Add to ~/.bashrc or ~/.zshrc:")
    print(f'   export GIT_REPO_URL="{repo_url}"')
    print(f'   export GIT_USERNAME="{username}"')
    print(f'   export GIT_TOKEN="your-token-here"')
    print("2. For Windows: Set via System Properties > Environment Variables")
    print("3. For Render.com: Add these in the Environment tab")
    
    return True

def check_remote_connection():
    """Check connection to the remote repository"""
    # Check if remote exists
    remotes, success = run_command("git remote")
    
    if not success or 'origin' not in remotes.split():
        print_status("Remote repository configuration", False, "Remote 'origin' is not configured.")
        return False
    
    # Check remote URL
    remote_url, success = run_command("git config --get remote.origin.url")
    
    if not success:
        print_status("Remote repository URL", False, "Failed to get remote URL.")
        return False
    
    repo_url = os.environ.get('GIT_REPO_URL', '')
    
    # Compare URLs ignoring credentials for security
    def normalize_url(url):
        if '@' in url:
            return 'https://' + url.split('@')[-1]
        return url
    
    expected_url = normalize_url(repo_url)
    current_url = normalize_url(remote_url)
    
    if expected_url != current_url:
        print_status("Remote repository URL match", False, 
                     f"URLs don't match: Expected '{expected_url}', got '{current_url}'")
        return False
    
    # Test connection
    fetch_output, success = run_command("git fetch origin --dry-run")
    
    if not success:
        print_status("Remote repository connection", False, "Failed to connect to remote repository.")
        return False
    
    print_status("Remote repository configuration", True)
    print_status("Remote repository URL match", True)
    print_status("Remote repository connection", True)
    return True

def setup_remote():
    """Set up the remote repository"""
    print_banner("Setting up Remote Repository", "-")
    
    repo_url = os.environ.get('GIT_REPO_URL', '')
    username = os.environ.get('GIT_USERNAME', '')
    token = os.environ.get('GIT_TOKEN', '')
    
    if not repo_url or not username or not token:
        print("Missing environment variables. Run with --fix to set them.")
        return False
    
    # Construct authenticated URL
    auth_url = repo_url.replace('https://', f'https://{username}:{token}@')
    
    # Check if remote exists
    remotes, _ = run_command("git remote")
    
    if 'origin' in remotes.split():
        # Update existing remote
        run_command(f'git remote set-url origin "{auth_url}"', show_output=True)
        print("Updated remote 'origin' URL.")
    else:
        # Add new remote
        run_command(f'git remote add origin "{auth_url}"', show_output=True)
        print("Added remote 'origin'.")
    
    # Test connection
    fetch_output, success = run_command("git fetch origin --dry-run", show_output=True)
    
    if not success:
        print("Failed to connect to remote repository. Check your credentials.")
        return False
    
    print("Successfully connected to remote repository.")
    return True

def check_push_capability():
    """Check if we can push to the remote repository"""
    # Create test file
    test_file = "git_health_check_test.txt"
    with open(test_file, 'w') as f:
        f.write(f"Git health check test file\n")
        f.write(f"Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Add and commit
    add_output, add_success = run_command(f"git add {test_file}")
    
    if not add_success:
        print_status("Git push capability", False, "Failed to add test file.")
        os.remove(test_file)
        return False
    
    commit_output, commit_success = run_command('git commit -m "Test commit for health check"')
    
    if not commit_success:
        print_status("Git push capability", False, "Failed to commit test file.")
        run_command(f"git reset -- {test_file}")
        os.remove(test_file)
        return False
    
    # Get current branch
    branch, _ = run_command("git branch --show-current")
    if not branch:
        branch = "main"
    
    # Try to push
    push_output, push_success = run_command(f"git push origin {branch}")
    
    # Clean up
    os.remove(test_file)
    run_command(f'git reset --soft HEAD~1')
    run_command(f"git restore --staged {test_file}")
    
    if not push_success:
        print_status("Git push capability", False, f"Failed to push to remote repository.")
        return False
    
    print_status("Git push capability", True)
    return True

def test_push_capability():
    """Test and fix push capability"""
    print_banner("Testing Push Capability", "-")
    
    # Create test file
    test_file = "git_health_check_test.txt"
    with open(test_file, 'w') as f:
        f.write(f"Git health check test file\n")
        f.write(f"Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"Created test file '{test_file}'.")
    
    # Add and commit
    run_command(f"git add {test_file}", show_output=True)
    run_command('git commit -m "Test commit for health check"', show_output=True)
    
    # Get current branch
    branch, _ = run_command("git branch --show-current")
    if not branch:
        branch = "main"
        
    print(f"Using branch: {branch}")
    
    # Try to push
    print("Attempting to push to remote repository...")
    push_output, push_success = run_command(f"git push origin {branch}", show_output=True)
    
    # Clean up
    print("Cleaning up test commit...")
    run_command(f'git reset --soft HEAD~1', show_output=True)
    run_command(f"git restore --staged {test_file}", show_output=True)
    os.remove(test_file)
    print(f"Removed test file '{test_file}'.")
    
    if not push_success:
        print("Failed to push to remote repository.")
        
        if "rejected" in push_output or "non-fast-forward" in push_output:
            print("Trying to fix by pulling first...")
            pull_output, pull_success = run_command(f"git pull --rebase origin {branch}", show_output=True)
            
            if pull_success:
                print("Pull successful. Retrying push...")
                push_output, push_success = run_command(f"git push origin {branch}", show_output=True)
                
                if push_success:
                    print("Push successful after pull!")
                    return True
            
            print("Consider using --force if you're sure your local changes should override remote.")
        
        return False
    
    print("Push successful!")
    return True

def check_repository_files():
    """Check if the repository has the correct file structure"""
    # Check data directory
    if not os.path.isdir(DATA_DIR):
        print_status("Data directory structure", False, f"'{DATA_DIR}' directory not found.")
        return False
    
    # Check meta.json
    meta_file = os.path.join(DATA_DIR, "meta.json")
    if not os.path.exists(meta_file):
        print_status("Meta file", False, f"'{meta_file}' not found.")
        return False
    
    # Check required subdirectories
    subdirs = ['caregivers', 'templates', 'calendars', 'shifts', 'checklists', 
               'activities', 'activity_categories']
    
    missing_dirs = []
    for subdir in subdirs:
        path = os.path.join(DATA_DIR, subdir)
        if not os.path.isdir(path):
            missing_dirs.append(subdir)
    
    if missing_dirs:
        print_status("Data subdirectories", False, f"Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print_status("Data directory structure", True)
    print_status("Meta file", True)
    print_status("Data subdirectories", True)
    return True

def check_import_modules():
    """Check if required Python modules can be imported"""
    required_modules = {
        'flask': 'Flask web framework',
        'werkzeug': 'WSGI utilities for Flask',
        'flask_wtf': 'Flask forms with CSRF protection',
        'flask_sqlalchemy': 'Flask SQLAlchemy integration'
    }
    
    missing_modules = []
    
    for module, description in required_modules.items():
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(f"{module} ({description})")
    
    if missing_modules:
        print_status("Required Python modules", False, f"Missing modules: {', '.join(missing_modules)}")
        return False
    
    print_status("Required Python modules", True)
    return True

def create_report():
    """Create a detailed health check report"""
    print_banner("Creating Health Check Report", "-")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        },
        "git": {
            "version": run_command("git --version")[0],
            "user": run_command("git config user.name")[0],
            "email": run_command("git config user.email")[0],
        },
        "repository": {
            "remote_url": run_command("git config --get remote.origin.url")[0],
            "current_branch": run_command("git branch --show-current")[0],
            "last_commit": run_command("git log -1 --oneline")[0]
        },
        "data_directory": {
            "exists": os.path.isdir(DATA_DIR),
            "subdirectories": []
        },
        "environment_variables": {
            var: "Set" if os.environ.get(var) else "Not set" for var in REQUIRED_ENV_VARS
        }
    }
    
    # Add data subdirectories
    if os.path.isdir(DATA_DIR):
        for item in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, item)):
                files = len([f for f in os.listdir(os.path.join(DATA_DIR, item)) if f.endswith('.json')])
                report["data_directory"]["subdirectories"].append({
                    "name": item,
                    "files": files
                })
    
    # Write report to file
    report_file = "git_health_check_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Detailed report saved to {report_file}")
    return report

def verify_render_compatibility():
    """Check for Render.com specific compatibility issues"""
    # Check for Procfile
    has_procfile = os.path.exists("Procfile")
    
    if not has_procfile:
        print_status("Procfile for Render.com", False, "Procfile not found.")
        return False
    
    # Check for requirements.txt
    has_requirements = os.path.exists("requirements.txt")
    
    if not has_requirements:
        print_status("requirements.txt", False, "requirements.txt not found.")
        return False
    
    # Check for runtime.txt
    has_runtime = os.path.exists("runtime.txt")
    
    if not has_runtime:
        print_status("runtime.txt", False, "runtime.txt not found for Python version specification.")
    else:
        print_status("runtime.txt", True)
    
    print_status("Procfile for Render.com", True)
    print_status("requirements.txt", True)
    
    return has_procfile and has_requirements

def main():
    parser = argparse.ArgumentParser(description="Git Health Check for AwaazTimetable")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues when possible")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--report", action="store_true", help="Generate detailed JSON report")
    args = parser.parse_args()
    
    print_banner("AwaazTimetable Git Health Check")
    
    # Show working directory
    print(f"Working directory: {os.getcwd()}")
    
    # Run checks
    checks = []
    
    # 1. Check Git installation
    git_installed = check_git_installation()
    checks.append(("Git installation", git_installed))
    
    if not git_installed:
        print("\nGit is not installed. Install Git before continuing.")
        sys.exit(1)
    
    # 2. Check Git configuration
    git_configured = check_git_configuration()
    checks.append(("Git configuration", git_configured))
    
    if not git_configured and args.fix:
        fix_git_configuration()
    
    # 3. Check local repository
    repo_ok = check_local_repo()
    checks.append(("Local repository", repo_ok))
    
    if not repo_ok and args.fix:
        setup_local_repo()
    
    # 4. Check repository files
    files_ok = check_repository_files()
    checks.append(("Repository files", files_ok))
    
    # 5. Check environment variables
    env_ok = check_env_variables()
    checks.append(("Environment variables", env_ok))
    
    if not env_ok and args.fix:
        set_env_variables()
    
    # 6. Check remote connection
    remote_ok = check_remote_connection()
    checks.append(("Remote connection", remote_ok))
    
    if not remote_ok and args.fix:
        setup_remote()
    
    # 7. Check push capability
    push_ok = check_push_capability()
    checks.append(("Push capability", push_ok))
    
    if not push_ok and args.fix:
        test_push_capability()
    
    # 8. Check module imports
    imports_ok = check_import_modules()
    checks.append(("Module imports", imports_ok))
    
    # 9. Check Render.com compatibility
    render_ok = verify_render_compatibility()
    checks.append(("Render.com compatibility", render_ok))
    
    # Generate report if requested
    if args.report:
        create_report()
    
    # Summary
    print_banner("Health Check Summary")
    
    all_checks_passed = all(result for _, result in checks)
    
    for name, result in checks:
        status_symbol = "✓" if result else "✗"
        status_color = "\033[92m" if result else "\033[91m"  # Green for pass, red for fail
        reset_color = "\033[0m"
        print(f"{status_color}{status_symbol}{reset_color} {name}")
    
    if all_checks_passed:
        print_banner("All checks PASSED! Git persistence is working correctly.", "*")
    else:
        print_banner("Some checks FAILED. Run with --fix to attempt automatic fixes.", "!")
        
        if not env_ok:
            print("\nMost common issues are related to environment variables:")
            print("1. Set GIT_REPO_URL to your GitHub repository URL")
            print("2. Set GIT_USERNAME to your GitHub username")
            print("3. Set GIT_TOKEN to your GitHub personal access token")
            print("\nFor Render.com, add these in the Environment tab of your service.")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 