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

def commit_and_push(message):
    """Commit all changes and push to remote"""
    try:
        log_banner(f"GIT OPERATION: {message}")
        logger.info(f"Starting Git operation in directory: {os.getcwd()}")
        
        # Diagnostic information
        log_banner("GIT ENVIRONMENT CHECK")
        
        # Log environment variables
        git_repo_url = os.environ.get('GIT_REPO_URL', 'Not set')
        git_username = os.environ.get('GIT_USERNAME', 'Not set')
        git_token = os.environ.get('GIT_TOKEN', 'Not set')
        
        # Mask any sensitive info before logging
        masked_repo_url = git_repo_url
        if '@' in git_repo_url:
            parts = git_repo_url.split('@')
            masked_repo_url = 'https://***:***@' + parts[1]
        
        logger.info(f"GIT_REPO_URL: {masked_repo_url}")
        logger.info(f"GIT_USERNAME: {git_username if git_username != 'Not set' else 'Not set'}")
        logger.info(f"GIT_TOKEN: {'Set (masked)' if git_token != 'Not set' else 'Not set'}")
        
        # Log Git configuration
        try:
            git_user = subprocess.check_output(['git', 'config', 'user.name']).decode('utf-8').strip()
            git_email = subprocess.check_output(['git', 'config', 'user.email']).decode('utf-8').strip()
            logger.info(f"Git user: {git_user} <{git_email}>")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Cannot get Git user config: {e}")
        
        # Log remote info
        try:
            remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8').strip()
            # Mask credentials in URL
            if '@' in remote_url:
                parts = remote_url.split('@')
                masked_url = 'https://***:***@' + parts[1]
                logger.info(f"Remote URL: {masked_url}")
            else:
                logger.info(f"Remote URL: {remote_url}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Cannot get remote URL: {e}")
        
        # Check if we're in a Git repository
        if not os.path.isdir('.git'):
            logger.error("Not in a Git repository! .git directory not found")
            return False
        
        # Add all changes
        log_banner("GIT ADD")
        logger.debug("Running: git add .")
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Git add error: {result.stderr}")
            print(f"Git add error: {result.stderr}")
            return False
        
        # Check if there are changes to commit
        try:
            logger.debug("Checking Git status")
            status = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
            if not status.strip():
                logger.info("No changes to commit")
                return True
            else:
                changes = status.strip().split('\n')
                logger.info(f"Changes to commit: {len(changes)} files")
                for change in changes:
                    logger.info(f"  {change}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Unable to check Git status: {e.stderr}")
            print(f"Unable to check Git status: {e.stderr}")
            return False
        
        # Commit changes
        log_banner("GIT COMMIT")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"{message} - Automated commit at {timestamp}"
        logger.info(f"Committing with message: {commit_msg}")
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Git commit error: {result.stderr}")
            print(f"Git commit error: {result.stderr}")
            return False
        else:
            logger.info("Local commit successful")
            
            # Log the commit hash
            try:
                commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
                logger.info(f"Commit hash: {commit_hash}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Unable to get commit hash: {e.stderr}")
        
        # Check if remote repo is configured
        log_banner("GIT REMOTE CHECK")
        try:
            logger.debug("Checking Git remotes")
            remotes = subprocess.check_output(['git', 'remote']).decode('utf-8').strip()
            if 'origin' not in remotes.split('\n'):
                logger.warning("No 'origin' remote found, skipping pull/push")
                print("No 'origin' remote found, skipping pull/push")
                return True  # Still return True since we committed locally
            
            # Get remote URL to verify it's configured
            remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8').strip()
            
            # Mask credentials in URL for logging
            if '@' in remote_url:
                parts = remote_url.split('@')
                masked_url = 'https://***:***@' + parts[1]
                logger.info(f"Remote URL configured: {masked_url}")
            else:
                logger.info(f"Remote URL configured: {remote_url}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Unable to check Git remotes: {e.stderr}")
            print(f"Unable to check Git remotes: {e.stderr}")
            return True  # Still return True since we committed locally
        
        # Get current branch name
        try:
            branch_name = subprocess.check_output(['git', 'branch', '--show-current']).decode('utf-8').strip()
            if not branch_name:
                branch_name = 'main'  # Default branch name if not available
            logger.info(f"Current branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            branch_name = 'main'  # Default branch name if command fails
            logger.info(f"Could not determine branch name, using default: {branch_name}")
        
        # Pull latest changes
        log_banner("GIT PULL")
        try:
            logger.info(f"Pulling latest changes from remote branch 'origin/{branch_name}'")
            result = subprocess.run(['git', 'pull', '--rebase', 'origin', branch_name], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Git pull error: {result.stderr}")
                print(f"Git pull error: {result.stderr}")
                # Try to resolve simple conflicts
                logger.info("Attempting to resolve conflicts")
                subprocess.run(['git', 'checkout', '--theirs', '.'], capture_output=True)
                subprocess.run(['git', 'add', '.'], capture_output=True)
                subprocess.run(['git', 'rebase', '--continue'], capture_output=True)
            else:
                logger.info("Pull successful or already up to date")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git pull failed: {e.stderr}")
            print(f"Git pull failed: {e.stderr}")
        
        # Push changes to remote
        log_banner("GIT PUSH")
        max_attempts = 3
        logger.info(f"Pushing changes to remote, max attempts: {max_attempts}")
        for attempt in range(max_attempts):
            try:
                logger.info(f"Push attempt {attempt+1}/{max_attempts} to branch 'origin/{branch_name}'")
                
                # Add -u flag to set up tracking for the first push
                if attempt == 0:
                    cmd = ['git', 'push', '-u', 'origin', branch_name]
                    logger.info(f"Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                else:
                    cmd = ['git', 'push', 'origin', branch_name]
                    logger.info(f"Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Log full command output regardless of success
                if result.stdout:
                    logger.info(f"Push stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"Push stderr: {result.stderr}")
                
                if result.returncode == 0:
                    log_banner("GIT PUSH SUCCESSFUL")
                    logger.info(f"Push successful to 'origin/{branch_name}'!")
                    print(f"Git push successful to branch '{branch_name}'!")
                    return True
                
                # Check for specific push errors
                error_msg = result.stderr
                logger.warning(f"Git push error (attempt {attempt+1}/{max_attempts}): {error_msg}")
                print(f"Git push error (attempt {attempt+1}/{max_attempts}): {error_msg}")
                
                # Handle different error cases
                if "rejected" in error_msg and "would be overwritten by merge" in error_msg:
                    # Handle non-fast-forward error (remote has changes that local doesn't)
                    logger.info("Attempting to pull and merge changes before pushing again")
                    subprocess.run(['git', 'pull', '--no-rebase', 'origin', branch_name], capture_output=True, text=True)
                elif "Repository not found" in error_msg:
                    logger.error("Repository not found error - check if the repository exists on GitHub")
                    logger.error("You need to create the repository at: " + remote_url)
                    break  # Stop trying, repository issue
                elif "Permission denied" in error_msg or "Authentication failed" in error_msg:
                    logger.error("Authentication error - check your Git credentials")
                    logger.error("Make sure GIT_USERNAME and GIT_TOKEN are set correctly")
                    # Add more detailed authentication diagnostics
                    if git_username == 'Not set' or git_token == 'Not set':
                        logger.error("GIT_USERNAME or GIT_TOKEN environment variables are not set")
                    break  # Stop trying, credentials issue
                
                if attempt < max_attempts - 1:
                    logger.info(f"Waiting 3 seconds before retry...")
                    time.sleep(3)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Git push failed (attempt {attempt+1}/{max_attempts}): {str(e)}")
                if e.stderr:
                    logger.warning(f"Error details: {e.stderr}")
                print(f"Git push failed (attempt {attempt+1}/{max_attempts}): {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(3)
        
        log_banner("GIT PUSH FAILED - LOCAL COMMIT ONLY")
        logger.warning("All push attempts failed, but changes are committed locally")
        print("All push attempts failed, but changes are committed locally")
        return True  # Return True since we at least committed locally
    except Exception as e:
        log_banner("GIT OPERATION ERROR")
        logger.error(f"Error in Git operations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Error in Git operations: {str(e)}")
        return False 