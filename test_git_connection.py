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
import time
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [GitTest] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitTest')

def log_banner(message):
    """Log a message with a prominent banner for visibility"""
    banner = "\n" + "=" * 70 + "\n" + " " + message.center(68) + " \n" + "=" * 70
    logger.info(banner)
    print(banner)

def verify_environment_variables():
    """Verify that required environment variables are set"""
    required_vars = ['GIT_REPO_URL', 'GIT_USERNAME', 'GIT_TOKEN']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        log_banner("MISSING ENVIRONMENT VARIABLES")
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these environment variables and try again")
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables and try again")
        return False
        
    return True

def verify_git_installation():
    """Verify that Git is installed and working"""
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        git_version = result.stdout.strip()
        logger.info(f"Git is installed: {git_version}")
        print(f"Git is installed: {git_version}")
        return True
    except FileNotFoundError:
        log_banner("GIT NOT FOUND")
        logger.error("Git is not installed or not in PATH")
        print("Git is not installed or not in PATH")
        return False
    except subprocess.CalledProcessError as e:
        log_banner("GIT ERROR")
        logger.error(f"Error checking Git version: {str(e)}")
        if e.stderr:
            logger.error(f"Error details: {e.stderr}")
        print(f"Error checking Git version: {str(e)}")
        return False

def setup_git_user():
    """Set up Git user for this repository"""
    try:
        git_username = os.environ.get('GIT_USERNAME', 'Awaaz Timetable Test')
        git_email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        
        # Set Git user name and email
        subprocess.run(['git', 'config', 'user.name', git_username], check=True)
        subprocess.run(['git', 'config', 'user.email', git_email], check=True)
        
        logger.info(f"Git user configured: {git_username} <{git_email}>")
        print(f"Git user configured: {git_username} <{git_email}>")
        return True
    except subprocess.CalledProcessError as e:
        log_banner("GIT CONFIG ERROR")
        logger.error(f"Error configuring Git user: {str(e)}")
        if e.stderr:
            logger.error(f"Error details: {e.stderr}")
        print(f"Error configuring Git user: {str(e)}")
        return False

def setup_git_credentials():
    """Set up Git credentials for authentication"""
    try:
        git_username = os.environ.get('GIT_USERNAME')
        git_token = os.environ.get('GIT_TOKEN')
        git_repo_url = os.environ.get('GIT_REPO_URL')
        
        if not (git_username and git_token and git_repo_url):
            logger.error("Missing Git credentials in environment variables")
            return False
            
        # Extract hostname from repo URL
        if 'github.com' in git_repo_url:
            host = 'github.com'
        else:
            if '://' in git_repo_url:
                host = git_repo_url.split('://')[1].split('/')[0]
            else:
                host = git_repo_url.split(':')[0]
                
        logger.info(f"Setting up Git credentials for host: {host}")
        
        # Use Git credential store
        subprocess.run(['git', 'config', 'credential.helper', 'store'], check=True)
        
        # Create credentials file in home directory
        cred_path = os.path.expanduser('~/.git-credentials')
        cred_line = f"https://{git_username}:{git_token}@{host}\n"
        
        with open(cred_path, 'w') as f:
            f.write(cred_line)
            
        logger.info(f"Git credentials stored in {cred_path}")
        print(f"Git credentials stored")
        return True
    except Exception as e:
        log_banner("CREDENTIAL SETUP ERROR")
        logger.error(f"Error setting up Git credentials: {str(e)}")
        print(f"Error setting up Git credentials: {str(e)}")
        return False

def test_remote_connection():
    """Test connection to the remote repository"""
    try:
        log_banner("TESTING REMOTE CONNECTION")
        logger.info("Testing connection to remote repository")
        
        # Try to fetch from remote repository
        result = subprocess.run(
            ['git', 'ls-remote', '--heads', 'origin'],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Successfully connected to remote repository")
        logger.info(f"Remote heads: {result.stdout}")
        print("Successfully connected to remote repository")
        return True
    except subprocess.CalledProcessError as e:
        log_banner("REMOTE CONNECTION ERROR")
        logger.error(f"Error connecting to remote repository: {str(e)}")
        if e.stderr:
            logger.error(f"Error details: {e.stderr}")
        print(f"Error connecting to remote repository: {str(e)}")
        return False

def test_push_capability(methods=None):
    """Test Git push capability using various methods"""
    if methods is None:
        methods = [
            {
                "name": "Standard push",
                "command": ['git', 'push', 'origin', 'HEAD']
            },
            {
                "name": "Push with explicit refspec",
                "command": ['git', 'push', 'origin', 'HEAD:refs/heads/main']
            },
            {
                "name": "Push current branch",
                "command": lambda: ['git', 'push', 'origin', subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('utf-8').strip()]
            },
            {
                "name": "Simple push",
                "command": ['git', 'push']
            }
        ]
    
    # Create a test file
    test_file = 'git_push_test.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        log_banner("TESTING GIT PUSH CAPABILITY")
        logger.info(f"Creating test file: {test_file}")
        
        # Create and add a test file
        with open(test_file, 'w') as f:
            f.write(f"Git push test file\nCreated at: {timestamp}\n")
            
        # Add file to Git
        subprocess.run(['git', 'add', test_file], check=True)
        
        # Commit the file
        commit_message = f"Test push capability - {timestamp}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        logger.info(f"Committed test file with message: {commit_message}")
        
        # Try each push method
        for method in methods:
            try:
                method_name = method["name"]
                command = method["command"]
                
                log_banner(f"TRYING PUSH METHOD: {method_name}")
                logger.info(f"Attempting to push using: {method_name}")
                
                # Handle callable commands (for dynamic commands)
                if callable(command):
                    try:
                        command = command()
                    except Exception as e:
                        logger.error(f"Error preparing command: {str(e)}")
                        continue
                
                logger.info(f"Executing: {' '.join(command)}")
                
                # Execute push command
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                log_banner(f"PUSH SUCCESSFUL: {method_name}")
                logger.info(f"Push successful using method: {method_name}")
                logger.info(f"Output: {result.stdout}")
                print(f"Push successful using method: {method_name}")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"Push failed using method: {method_name}")
                if e.stderr:
                    logger.warning(f"Error details: {e.stderr}")
                # Continue trying other methods
        
        # If we reach here, all methods failed
        log_banner("ALL PUSH METHODS FAILED")
        logger.error("Failed to push using all available methods")
        print("Failed to push using all available methods")
        return False
                
    except Exception as e:
        log_banner("PUSH TEST ERROR")
        logger.error(f"Error during push capability test: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Error during push capability test: {str(e)}")
        return False
    finally:
        # Clean up - remove the test file (but don't worry if it fails)
        try:
            if os.path.exists(test_file):
                os.remove(test_file)
        except:
            pass

def main():
    """Main function to run the Git connection test"""
    log_banner("GIT CONNECTION TEST")
    
    steps = [
        ("Verifying environment variables", verify_environment_variables),
        ("Verifying Git installation", verify_git_installation),
        ("Setting up Git user", setup_git_user),
        ("Setting up Git credentials", setup_git_credentials),
        ("Testing remote connection", test_remote_connection),
        ("Testing push capability", test_push_capability)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        log_banner(f"STEP: {step_name}")
        try:
            result = step_func()
            results[step_name] = result
            
            if not result:
                logger.error(f"Step failed: {step_name}")
                print(f"Step failed: {step_name}")
                break
        except Exception as e:
            logger.error(f"Error in step {step_name}: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Error in step {step_name}: {str(e)}")
            results[step_name] = False
            break
    
    # Display summary
    log_banner("TEST RESULTS SUMMARY")
    all_passed = all(results.values())
    
    for step_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{step_name}: {status}")
        print(f"{step_name}: {status}")
    
    if all_passed:
        log_banner("ALL TESTS PASSED")
        logger.info("Git connection test completed successfully")
        print("Git connection test completed successfully")
        return 0
    else:
        log_banner("SOME TESTS FAILED")
        logger.error("Git connection test failed")
        print("Git connection test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 