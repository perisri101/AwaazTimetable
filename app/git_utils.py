import os
import subprocess
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [GitDB] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitDB')

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
                
                # Change HTTPS URL to include authentication
                if repo_url.startswith('https://'):
                    authenticated_url = f'https://{username}:{token[:4]}...@' + repo_url[8:]  # Mask token for logging
                    logger.info(f"Setting authenticated remote URL: {authenticated_url[:15]}... (masked for security)")
                    subprocess.run(['git', 'remote', 'set-url', 'origin', f'https://{username}:{token}@{repo_url[8:]}'])
            except subprocess.CalledProcessError:
                logger.warning("No Git remote origin found, remote operations will be disabled")
                print("No Git remote origin found, remote operations will be disabled")
        
        logger.info("Git credentials setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Git setup failed: {str(e)}")
        print(f"Git setup failed, persistence through Git will be disabled: {str(e)}")
        return False

def commit_and_push(message):
    """Commit all changes and push to remote"""
    try:
        logger.info(f"Starting Git operation: {message}")
        
        # Add all changes
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
                logger.info(f"Changes to commit: {len(status.strip().split(os.linesep))} files")
        except subprocess.CalledProcessError:
            logger.warning("Unable to check Git status, skipping commit")
            print("Unable to check Git status, skipping commit")
            return False
        
        # Commit changes
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
        
        # Check if remote repo is configured
        try:
            logger.debug("Checking Git remotes")
            remotes = subprocess.check_output(['git', 'remote']).decode('utf-8').strip()
            if 'origin' not in remotes.split('\n'):
                logger.warning("No 'origin' remote found, skipping pull/push")
                print("No 'origin' remote found, skipping pull/push")
                return True  # Still return True since we committed locally
            
            # Get remote URL to verify it's configured
            remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8').strip()
            logger.info(f"Remote URL configured: {remote_url[:8]}... (masked for security)")
        except subprocess.CalledProcessError:
            logger.warning("Unable to check Git remotes, skipping pull/push")
            print("Unable to check Git remotes, skipping pull/push")
            return True  # Still return True since we committed locally
        
        # Get current branch name
        try:
            branch_name = subprocess.check_output(['git', 'branch', '--show-current']).decode('utf-8').strip()
            if not branch_name:
                branch_name = 'main'  # Default branch name if not available
            logger.info(f"Current branch: {branch_name}")
        except subprocess.CalledProcessError:
            branch_name = 'main'  # Default branch name if command fails
            logger.info(f"Could not determine branch name, using default: {branch_name}")
        
        # Pull latest changes
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
        except subprocess.CalledProcessError:
            logger.warning("Git pull failed, continuing with local commit only")
            print("Git pull failed, continuing with local commit only")
        
        # Push changes to remote
        max_attempts = 3
        logger.info(f"Pushing changes to remote, max attempts: {max_attempts}")
        for attempt in range(max_attempts):
            try:
                logger.info(f"Push attempt {attempt+1}/{max_attempts} to branch 'origin/{branch_name}'")
                
                # Add -u flag to set up tracking for the first push
                if attempt == 0:
                    result = subprocess.run(['git', 'push', '-u', 'origin', branch_name], capture_output=True, text=True)
                else:
                    result = subprocess.run(['git', 'push', 'origin', branch_name], capture_output=True, text=True)
                
                if result.returncode == 0:
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
                elif "Permission denied" in error_msg:
                    logger.error("Permission denied error - check Git credentials")
                    break  # Stop trying, credentials issue
                
                if attempt < max_attempts - 1:
                    logger.info(f"Waiting 3 seconds before retry...")
                    time.sleep(3)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Git push failed (attempt {attempt+1}/{max_attempts}): {str(e)}")
                print(f"Git push failed (attempt {attempt+1}/{max_attempts}): {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(3)
        
        logger.warning("All push attempts failed, but changes are committed locally")
        print("All push attempts failed, but changes are committed locally")
        return True  # Return True since we at least committed locally
    except Exception as e:
        logger.error(f"Error in Git operations: {str(e)}")
        print(f"Error in Git operations: {str(e)}")
        return False 