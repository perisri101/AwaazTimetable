import os
import subprocess
import time
from datetime import datetime
import logging
import traceback
import sys
import urllib.parse  # Add this import for URL encoding

# Configure logging with more details
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum information
    format='[%(asctime)s] [GitDB] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitDB')

# Add a stream handler to output to stdout as well
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logging.Formatter('[%(asctime)s] [GitDB] %(levelname)s: %(message)s'))
logger.addHandler(stdout_handler)

def log_banner(message):
    """Log a message with a prominent banner for visibility"""
    banner = "\n" + "=" * 70 + "\n" + " " + message.center(68) + " \n" + "=" * 70
    logger.info(banner)
    print(banner)

def run_git_diagnostic():
    """Run comprehensive diagnostics on Git setup and connection"""
    logger.info("=============== GIT REPOSITORY DIAGNOSTICS ===============")
    
    # Check Git version
    try:
        git_version = subprocess.check_output(['git', '--version']).decode('utf-8').strip()
        logger.info(f"Git version: {git_version}")
    except Exception as e:
        logger.error(f"Error checking Git version: {str(e)}")
    
    # Check if .git directory exists
    if os.path.isdir('.git'):
        logger.info(".git directory exists")
    else:
        logger.error("No .git directory found - Git operations will fail!")
        return False
    
    # Check Git configuration
    try:
        username = subprocess.check_output(['git', 'config', 'user.name']).decode('utf-8').strip()
        email = subprocess.check_output(['git', 'config', 'user.email']).decode('utf-8').strip()
        logger.info(f"Git user configured: {username} <{email}>")
    except Exception as e:
        logger.warning(f"Git user configuration missing: {str(e)}")
    
    # Check remote configuration
    try:
        remotes = subprocess.check_output(['git', 'remote', '-v']).decode('utf-8')
        logger.info(f"Git remotes:\n{remotes}")
        
        if 'origin' not in remotes:
            logger.error("No 'origin' remote configured - Push operations will fail!")
        
        # Check if remote URL is accessible
        try:
            # Safe way to test connection without showing credentials in logs
            subprocess.check_output(['git', 'ls-remote', '--heads', 'origin'], stderr=subprocess.PIPE)
            logger.info("Successfully connected to remote repository!")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode('utf-8')
            logger.error(f"Unable to connect to remote repository: {error_output}")
            
            # Check for specific error types
            if "Repository not found" in error_output:
                logger.error("DIAGNOSIS: The repository does not exist or is not accessible with current credentials")
                logger.error("ACTION NEEDED: Create the repository or check your access permissions")
            elif "could not read Username" in error_output or "Authentication failed" in error_output:
                logger.error("DIAGNOSIS: Authentication issue - credentials not provided or invalid")
                logger.error("ACTION NEEDED: Set GIT_USERNAME and GIT_TOKEN environment variables")
            elif "not found" in error_output:
                logger.error("DIAGNOSIS: Repository URL is incorrect or repository doesn't exist")
                logger.error("ACTION NEEDED: Verify the repository URL and create it if needed")
    except Exception as e:
        logger.error(f"Error checking remote configuration: {str(e)}")
    
    # Check environment variables
    logger.info("Checking environment variables:")
    git_repo_url = os.environ.get('GIT_REPO_URL')
    git_username = os.environ.get('GIT_USERNAME')
    git_token = os.environ.get('GIT_TOKEN')
    
    if git_repo_url:
        # Mask the URL if it contains credentials
        masked_url = git_repo_url
        if '@' in git_repo_url:
            # URL has credentials embedded - mask them
            parts = git_repo_url.split('@')
            masked_url = 'https://***:***@' + parts[1]
        logger.info(f"GIT_REPO_URL: {masked_url}")
    else:
        logger.warning("GIT_REPO_URL not set")
    
    logger.info(f"GIT_USERNAME: {'Set' if git_username else 'Not set'}")
    logger.info(f"GIT_TOKEN: {'Set' if git_token else 'Not set'}")
    
    # Check latest commit and branch status
    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current']).decode('utf-8').strip()
        logger.info(f"Current branch: {branch}")
        
        last_commit = subprocess.check_output(['git', 'log', '-1', '--oneline']).decode('utf-8').strip()
        logger.info(f"Latest commit: {last_commit}")
    except Exception as e:
        logger.warning(f"Error getting Git branch or commit info: {str(e)}")
    
    logger.info("=============== END DIAGNOSTICS ===============")
    return True

def setup_git_credentials(repo_path):
    """Setup git credentials for automated commits"""
    try:
        logger.info(f"Setting up Git credentials in {repo_path}")
        email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
        
        os.chdir(repo_path)
        logger.info(f"Configuring Git user: {name} <{email}>")
        subprocess.run(['git', 'config', 'user.email', email])
        subprocess.run(['git', 'config', 'user.name', name])
        
        # If using GitHub token for authentication
        if 'GIT_TOKEN' in os.environ and 'GIT_USERNAME' in os.environ:
            token = os.environ.get('GIT_TOKEN')
            username = os.environ.get('GIT_USERNAME')
            logger.info(f"GitHub token found for user: {username}")
            
            # Try to get the remote URL safely
            try:
                repo_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8').strip()
                logger.info(f"Found remote URL: {repo_url[:8]}... (masked for security)")
                
                # Change HTTPS URL to include authentication using credentials helper instead
                # This is more reliable than embedding credentials in the URL
                if repo_url.startswith('https://'):
                    logger.info("Setting up Git credentials using credential helper")
                    
                    # Set Git to use credential helper
                    subprocess.run(['git', 'config', 'credential.helper', 'store'])
                    
                    # Extract the hostname (github.com)
                    host = repo_url.split('//')[1].split('/')[0]
                    logger.info(f"Using credentials for host: {host}")
                    
                    # Create credentials file
                    cred_path = os.path.expanduser('~/.git-credentials')
                    
                    # URL encode the username and token for safety
                    encoded_username = urllib.parse.quote(username)
                    encoded_token = urllib.parse.quote(token)
                    
                    # Create credentials line
                    cred_line = f"https://{encoded_username}:{encoded_token}@{host}\n"
                    
                    # Write credentials to file
                    with open(cred_path, 'w') as f:
                        f.write(cred_line)
                    
                    logger.info("Git credentials stored using credential helper")
                    
                    # Test the connection
                    try:
                        subprocess.check_output(['git', 'ls-remote', '--heads', 'origin'], stderr=subprocess.PIPE)
                        logger.info("Successfully authenticated with remote repository!")
                    except subprocess.CalledProcessError as e:
                        error_msg = e.stderr.decode('utf-8')
                        logger.error(f"Failed to authenticate with remote repository: {error_msg}")
                        
                        if "Repository not found" in error_msg:
                            logger.error("The repository doesn't exist or you don't have access to it")
                            logger.error("Make sure you created the repository on GitHub")
                        elif "Authentication failed" in error_msg:
                            logger.error("Authentication failed - check your username and token")
                            logger.error("Make sure your token has 'repo' permissions")
                            
                            # Try alternative approach using Git credential.helper directly
                            logger.info("Trying alternative authentication approach...")
                            
                            # Clean up existing auth
                            subprocess.run(['git', 'config', '--unset', 'credential.helper'])
                            
                            # Set up credentials using environment variables
                            # This approach uses environment variables directly
                            os.environ['GIT_ASKPASS'] = 'echo'
                            os.environ['GIT_USERNAME'] = username
                            os.environ['GIT_PASSWORD'] = token
                            
                            # Set remote without credentials in URL
                            subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url])
                            logger.info(f"Set remote URL to {repo_url}")
                            
                            # Test connection
                            try:
                                subprocess.check_output(['git', 'ls-remote', '--heads', 'origin'], stderr=subprocess.PIPE, env=os.environ)
                                logger.info("Successfully authenticated with alternative method!")
                            except subprocess.CalledProcessError as inner_e:
                                logger.error(f"Alternative authentication also failed: {inner_e.stderr.decode('utf-8')}")
            except subprocess.CalledProcessError:
                logger.warning("No Git remote origin found, remote operations will be disabled")
                print("No Git remote origin found, remote operations will be disabled")
                
                # Try to get the repo URL from environment
                repo_url = os.environ.get('GIT_REPO_URL')
                if repo_url:
                    logger.info(f"Using GIT_REPO_URL from environment: {repo_url[:8]}... (masked for security)")
                    
                    # Set up without embedding credentials in URL
                    subprocess.run(['git', 'remote', 'add', 'origin', repo_url])
                    logger.info("Added 'origin' remote from environment variable")
                    
                    # Set up credentials store
                    subprocess.run(['git', 'config', 'credential.helper', 'store'])
                    
                    # Extract the hostname (github.com)
                    host = repo_url.split('//')[1].split('/')[0]
                    
                    # URL encode the username and token for safety
                    encoded_username = urllib.parse.quote(username)
                    encoded_token = urllib.parse.quote(token)
                    
                    # Create credentials line
                    cred_path = os.path.expanduser('~/.git-credentials')
                    cred_line = f"https://{encoded_username}:{encoded_token}@{host}\n"
                    
                    # Write credentials to file
                    with open(cred_path, 'w') as f:
                        f.write(cred_line)
                    
                    logger.info("Git credentials stored for new remote")
        
        logger.info("Git credentials setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Git setup failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Git setup failed, persistence through Git will be disabled: {str(e)}")
        return False

def check_and_fix_detached_head(repo_path):
    """
    Check if the repository is in a detached HEAD state and fix it
    """
    try:
        logger.info("Checking if repository is in detached HEAD state")
        
        # Check if HEAD is detached
        try:
            # This command will succeed if HEAD is attached to a branch
            subprocess.check_output(['git', 'symbolic-ref', 'HEAD'], stderr=subprocess.PIPE, cwd=repo_path)
            logger.info("Repository is on a proper branch")
            return True
        except subprocess.CalledProcessError:
            # HEAD is detached, need to fix it
            logger.warning("Repository is in DETACHED HEAD state! Attempting to fix...")
            
            # Get the current commit
            current_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_path).decode('utf-8').strip()
            logger.info(f"Current commit: {current_commit}")
            
            # Check if main branch exists
            branches = subprocess.check_output(['git', 'branch'], cwd=repo_path).decode('utf-8').split('\n')
            main_branches = [b.strip('* ') for b in branches if 'main' in b or 'master' in b]
            
            if main_branches:
                branch_name = main_branches[0]
                logger.info(f"Found existing branch: {branch_name}")
                
                # Checkout the existing branch
                subprocess.run(['git', 'checkout', branch_name], cwd=repo_path, check=True)
                logger.info(f"Checked out branch: {branch_name}")
                
                # Ensure the branch points to our current commit (if ahead)
                subprocess.run(['git', 'reset', '--hard', current_commit], cwd=repo_path, check=True)
                logger.info(f"Reset {branch_name} to current commit: {current_commit}")
            else:
                # Create a new main branch at the current commit
                logger.info("No main/master branch found, creating new 'main' branch")
                subprocess.run(['git', 'checkout', '-b', 'main'], cwd=repo_path, check=True)
                logger.info("Created and checked out new 'main' branch")
            
            # Verify we're now on a branch
            branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=repo_path).decode('utf-8').strip()
            logger.info(f"Repository is now on branch: {branch}")
            return True
    except Exception as e:
        logger.error(f"Error fixing detached HEAD: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def commit_and_push(message):
    """
    Commit and push changes to the Git repository
    Returns True if the operation was successful, False otherwise
    """
    try:
        # Log the intent to commit
        log_banner("GIT COMMIT STARTED")
        logger.info(f"Attempting to commit with message: {message}")
        print(f"Attempting to commit with message: {message}")
        
        # Get the repository path
        repo_path = os.path.dirname(os.path.dirname(__file__))
        logger.info(f"Repository path: {repo_path}")
        
        # Verify we're working with a valid Git repository
        if not os.path.isdir(os.path.join(repo_path, '.git')):
            logger.error(f"No .git directory found at {repo_path} - Git operations will fail!")
            print(f"No .git directory found at {repo_path} - Git operations will fail!")
            return False
        
        # Check and fix detached HEAD state if necessary
        if not check_and_fix_detached_head(repo_path):
            logger.warning("Failed to fix detached HEAD state, but continuing with commit attempt")
            
        # Verify and setup Git remote if needed
        try:
            # Check if remote origin is configured
            remote_result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_output = remote_result.stdout
            logger.info(f"Git remote configuration: {remote_output}")
            
            if 'origin' not in remote_output:
                # Origin remote is not configured, try to add it using environment variable
                logger.warning("No 'origin' remote configured - attempting to set up")
                git_repo_url = os.environ.get('GIT_REPO_URL')
                
                if git_repo_url:
                    logger.info(f"Setting up 'origin' remote using GIT_REPO_URL environment variable")
                    # Using masked URL in logs for security
                    masked_url = git_repo_url
                    if '@' in git_repo_url:
                        parts = git_repo_url.split('@')
                        masked_url = 'https://***:***@' + parts[1]
                    logger.info(f"Using repo URL: {masked_url}")
                    
                    # Add the remote origin
                    subprocess.run(
                        ['git', 'remote', 'add', 'origin', git_repo_url],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("Added 'origin' remote successfully")
                else:
                    logger.error("Cannot set up 'origin' remote: GIT_REPO_URL environment variable not found")
                    logger.error("Will commit locally only")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error checking or setting up Git remote: {str(e)}")
            if e.stderr:
                logger.warning(f"Error details: {e.stderr}")
            # Continue anyway - we'll at least try to commit locally
            
        # Check if there are changes to commit
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                logger.info("No changes to commit")
                print("No changes to commit")
                return True  # Consider this a success since there's nothing to commit
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git status check failed: {str(e)}")
            if e.stderr:
                logger.warning(f"Error details: {e.stderr}")
            print(f"Git status check failed: {str(e)}")
            # Continue anyway - we'll let the commit command decide if there's something to commit
        
        # Add all changes, including new files
        try:
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Added all changes to staging area")
            print("Added all changes to staging area")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git add failed: {str(e)}")
            if e.stderr:
                logger.warning(f"Error details: {e.stderr}")
            print(f"Git add failed: {str(e)}")
            # Continue anyway - maybe some files were added successfully
        
        # Commit the changes
        try:
            # Commit with the provided message
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            commit_message = f"{message} - Automated commit at {timestamp}"
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message, '--allow-empty'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Changes committed successfully")
            logger.info(f"Commit details: {result.stdout}")
            print("Changes committed successfully")
            
            # Check if we're connected to a remote repository
            git_repo_url = os.environ.get('GIT_REPO_URL')
            git_username = os.environ.get('GIT_USERNAME')
            git_token = os.environ.get('GIT_TOKEN')
            
            if not git_repo_url:
                logger.warning("No GIT_REPO_URL environment variable found. Skipping push.")
                print("No GIT_REPO_URL environment variable found. Skipping push.")
                return True  # We committed successfully, just didn't push
                
            # Push changes if we have credentials
            if git_username and git_token:
                log_banner("GIT PUSH STARTED")
                logger.info("Pushing changes to remote repository")
                print("Pushing changes to remote repository")
                
                # Maximum number of push attempts
                max_attempts = 3
                
                # Get the current branch name
                branch_result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                current_branch = branch_result.stdout.strip()
                
                # If we're in a detached HEAD state, we need to use a different approach
                if current_branch == 'HEAD':
                    logger.warning("We are in a detached HEAD state, will try to push to main branch")
                    current_branch = 'main'  # Default to main branch
                
                logger.info(f"Current branch is '{current_branch}', preparing to push")
                
                # Try to push several times with different methods
                push_methods = [
                    # Method 1: Push to specific branch
                    ['git', 'push', 'origin', f"{current_branch}"],
                    # Method 2: Push with explicit refspec
                    ['git', 'push', 'origin', f"HEAD:refs/heads/{current_branch}"],
                    # Method 3: Simple push with upstream tracking
                    ['git', 'push', '-u', 'origin', current_branch],
                    # Method 4: Force push if needed
                    ['git', 'push', '-f', 'origin', current_branch],
                    # Method 5: Simple push
                    ['git', 'push']
                ]
                
                success = False
                
                for method_index, push_command in enumerate(push_methods):
                    if success:
                        break
                        
                    for attempt in range(max_attempts):
                        try:
                            logger.info(f"Trying push method {method_index+1}/{len(push_methods)}, attempt {attempt+1}/{max_attempts}")
                            logger.info(f"Executing push command: {' '.join(push_command)}")
                            
                            push_result = subprocess.run(
                                push_command,
                                cwd=repo_path,
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            
                            log_banner("GIT PUSH SUCCESSFUL")
                            logger.info("Changes pushed to remote repository")
                            logger.info(f"Push details: {push_result.stdout}")
                            print("Changes pushed to remote repository")
                            success = True
                            break
                        except subprocess.CalledProcessError as e:
                            logger.warning(f"Git push failed (method {method_index+1}, attempt {attempt+1}): {str(e)}")
                            if e.stderr:
                                logger.warning(f"Error details: error: {e.stderr}")
                                
                                # Check for specific error messages and provide better feedback
                                stderr = e.stderr
                                if "Repository not found" in stderr:
                                    logger.error("DIAGNOSIS: The repository does not exist or is not accessible")
                                    logger.error("ACTION NEEDED: Verify the repository exists at the specified URL")
                                elif "Authentication failed" in stderr:
                                    logger.error("DIAGNOSIS: Authentication failed - invalid credentials")
                                    logger.error("ACTION NEEDED: Check your GIT_USERNAME and GIT_TOKEN")
                                elif "not a full refname" in stderr or "starting with \"refs/\"" in stderr:
                                    logger.error("DIAGNOSIS: Invalid Git reference name format")
                                    logger.error("ACTION NEEDED: Trying alternative push methods")
                                elif "detached HEAD" in stderr:
                                    logger.error("DIAGNOSIS: Repository is in detached HEAD state")
                                    logger.error("ACTION NEEDED: Will try to fix this in the next method")
                                elif "fetch first" in stderr or "rejected" in stderr:
                                    logger.error("DIAGNOSIS: Remote has changes that we don't have locally")
                                    logger.error("ACTION NEEDED: Trying to pull first before push")
                                    
                                    # Try to pull changes first
                                    try:
                                        logger.info("Attempting to pull changes from remote...")
                                        subprocess.run(
                                            ['git', 'pull', 'origin', current_branch, '--allow-unrelated-histories'],
                                            cwd=repo_path,
                                            capture_output=True,
                                            text=True,
                                            check=True
                                        )
                                        logger.info("Pull successful, retrying push")
                                        # Continue to next attempt which will retry the push
                                    except subprocess.CalledProcessError as pull_e:
                                        logger.warning(f"Pull failed: {pull_e.stderr}")
                                        # Continue to next method
                            
                            print(f"Git push failed (method {method_index+1}, attempt {attempt+1}): Check logs for details")
                            if attempt < max_attempts - 1:
                                logger.info(f"Waiting 3 seconds before retry...")
                                time.sleep(3)
                
                if not success:
                    log_banner("ALL GIT PUSH METHODS FAILED - LOCAL COMMIT ONLY")
                    logger.warning("All push attempts failed, but changes are committed locally")
                    print("All push attempts failed, but changes are committed locally")
                    return True  # Return True since we at least committed locally
            else:
                logger.warning("Git credentials not configured. Skipping push.")
                print("Git credentials not configured. Skipping push.")
                return True  # We committed successfully, just didn't push
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {str(e)}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            print(f"Git commit failed: {str(e)}")
            return False
        
    except Exception as e:
        log_banner("GIT OPERATION ERROR")
        logger.error(f"Error in Git operations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Error in Git operations: {str(e)}")
        return False 