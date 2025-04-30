#!/usr/bin/env python3
"""
Emergency fix script for Git authentication issues on Render.com.
This script directly fixes authentication problems by properly URL-encoding
credentials and setting up Git credential store.

Usage: python fix_git_auth.py
"""

import os
import subprocess
import sys
import urllib.parse

def print_banner(message):
    """Print a formatted banner message"""
    banner = "\n" + "=" * 80 + "\n" + " " + message.center(78) + " \n" + "=" * 80
    print(banner)

def run_command(cmd, show_output=True):
    """Run a command and return its output"""
    if show_output:
        print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if show_output and result.stdout:
            print(f"Output: {result.stdout}")
        return result.stdout.strip(), True
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"Error: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
        return e.stderr.strip() if e.stderr else "", False

def check_environment_variables():
    """Check if required environment variables are set"""
    print_banner("CHECKING ENVIRONMENT VARIABLES")
    
    required_vars = ['GIT_REPO_URL', 'GIT_USERNAME', 'GIT_TOKEN']
    all_present = True
    
    for var in required_vars:
        value = os.environ.get(var, '')
        if not value:
            print(f"{var}: Not set ❌")
            all_present = False
        else:
            if var == 'GIT_TOKEN':
                display = value[:4] + '...' + value[-4:] if len(value) > 8 else '****'
                print(f"{var}: {display} ✅")
            else:
                print(f"{var}: {value} ✅")
    
    return all_present

def fix_git_authentication():
    """Fix Git authentication using credential store"""
    print_banner("FIXING GIT AUTHENTICATION")
    
    # Get environment variables
    repo_url = os.environ.get('GIT_REPO_URL')
    username = os.environ.get('GIT_USERNAME')
    token = os.environ.get('GIT_TOKEN')
    
    if not repo_url or not username or not token:
        print("ERROR: Required environment variables are missing!")
        return False
    
    # 1. Remove any existing authentication configuration
    print("Removing any existing Git credential configuration...")
    run_command("git config --unset credential.helper", show_output=False)
    
    # 2. Configure Git to use credential store
    print("Setting up Git credential store...")
    run_command("git config credential.helper store")
    
    # 3. Make sure the remote is set correctly without credentials
    # First, check if remote exists
    remote_exists, _ = run_command("git remote | grep -q '^origin$' && echo 'yes' || echo 'no'", show_output=False)
    
    # If remote already exists, update it
    if remote_exists.strip() == 'yes':
        print("Updating existing remote...")
        run_command(f"git remote set-url origin {repo_url}")
    else:
        print("Adding new remote...")
        run_command(f"git remote add origin {repo_url}")
    
    # 4. Create credentials file with URL-encoded values
    home_dir = os.path.expanduser('~')
    cred_path = os.path.join(home_dir, '.git-credentials')
    
    # URL encode the username and token
    encoded_username = urllib.parse.quote(username)
    encoded_token = urllib.parse.quote(token)
    
    # Extract hostname from repo URL
    if '://' in repo_url:
        hostname = repo_url.split('://')[1].split('/')[0]
    else:
        hostname = repo_url.split(':')[0]
    
    # Create credentials line
    cred_line = f"https://{encoded_username}:{encoded_token}@{hostname}\n"
    
    print(f"Writing credentials to {cred_path}...")
    with open(cred_path, 'w') as f:
        f.write(cred_line)
    
    # Set proper permissions
    os.chmod(cred_path, 0o600)
    
    print("Git credentials stored successfully!")
    
    # 5. Test connection
    print("Testing connection to remote repository...")
    output, success = run_command("git ls-remote --heads origin")
    
    if success:
        print("✅ Successfully connected to remote repository!")
        return True
    else:
        print("❌ Connection test failed!")
        print("Trying alternative approach...")
        
        # Alternative approach using environment variables
        os.environ['GIT_ASKPASS'] = 'echo'
        os.environ['GIT_USERNAME'] = username
        os.environ['GIT_PASSWORD'] = token
        
        alt_cmd = "GIT_ASKPASS=echo " + \
                 f"GIT_USERNAME={username} " + \
                 f"GIT_PASSWORD={token} " + \
                 "git ls-remote --heads origin"
        
        alt_output, alt_success = run_command(alt_cmd)
        
        if alt_success:
            print("✅ Successfully connected using alternative method!")
            
            # Set up this method permanently
            print("Setting up alternative authentication method permanently...")
            with open(os.path.join(home_dir, '.gitconfig'), 'a') as f:
                f.write("\n[credential]\n")
                f.write("    helper = !f() { echo username=${GIT_USERNAME}; echo password=${GIT_PASSWORD}; }; f\n")
            
            # Create a wrapper script for Git operations
            wrapper_path = os.path.join(home_dir, 'git_wrapper.sh')
            with open(wrapper_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"export GIT_USERNAME={username}\n")
                f.write(f"export GIT_PASSWORD={token}\n")
                f.write('git "$@"\n')
            
            # Make it executable
            os.chmod(wrapper_path, 0o755)
            
            print(f"Created git wrapper script at {wrapper_path}")
            print("You can use this script instead of git for operations requiring authentication")
            
            return True
        else:
            print("❌ All authentication methods failed!")
            return False

def test_git_push():
    """Test if Git push works now"""
    print_banner("TESTING GIT PUSH")
    
    # Create a test file
    test_file = 'git_auth_fix_test.txt'
    with open(test_file, 'w') as f:
        f.write("Git authentication fix test\n")
    
    # Try to commit and push it
    print("Adding test file...")
    run_command(f"git add {test_file}")
    
    print("Committing test file...")
    run_command('git commit -m "Test commit for authentication fix"')
    
    print("Pushing to remote repository...")
    output, success = run_command("git push origin HEAD")
    
    # Clean up
    os.remove(test_file)
    
    if success:
        print("✅ Git push successful! Authentication is working correctly.")
        return True
    else:
        print("❌ Git push failed!")
        print(f"Error: {output}")
        return False

def main():
    print_banner("GIT AUTHENTICATION FIX TOOL")
    
    # Check environment variables
    env_ok = check_environment_variables()
    if not env_ok:
        print("ERROR: Required environment variables are missing!")
        print("Please set GIT_REPO_URL, GIT_USERNAME, and GIT_TOKEN")
        return 1
    
    # Fix Git authentication
    auth_ok = fix_git_authentication()
    if not auth_ok:
        print("Failed to fix Git authentication!")
        return 1
    
    # Test Git push
    push_ok = test_git_push()
    
    # Summary
    print_banner("SUMMARY")
    print(f"Environment Variables: {'✅ OK' if env_ok else '❌ Missing some variables'}")
    print(f"Git Authentication: {'✅ Fixed' if auth_ok else '❌ Not fixed'}")
    print(f"Git Push Test: {'✅ Successful' if push_ok else '❌ Failed'}")
    
    if push_ok:
        print("\nGit authentication has been successfully fixed!")
        print("Your application should now be able to push changes to the remote repository.")
    else:
        print("\nGit authentication fix was not completely successful.")
        print("Please check the logs for more information.")
    
    return 0 if push_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 