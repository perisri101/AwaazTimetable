import os
import subprocess
import time
from datetime import datetime

def setup_git_credentials(repo_path):
    """Setup git credentials for automated commits"""
    try:
        email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
        name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
        
        os.chdir(repo_path)
        subprocess.run(['git', 'config', 'user.email', email])
        subprocess.run(['git', 'config', 'user.name', name])
        
        # If using GitHub token for authentication
        if 'GIT_TOKEN' in os.environ and 'GIT_USERNAME' in os.environ:
            token = os.environ.get('GIT_TOKEN')
            username = os.environ.get('GIT_USERNAME')
            
            # Try to get the remote URL safely
            try:
                repo_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                
                # Change HTTPS URL to include authentication
                if repo_url.startswith('https://'):
                    authenticated_url = f'https://{username}:{token}@' + repo_url[8:]
                    subprocess.run(['git', 'remote', 'set-url', 'origin', authenticated_url])
            except subprocess.CalledProcessError:
                print("No Git remote origin found, remote operations will be disabled")
        
        return True
    except Exception as e:
        print(f"Git setup failed, persistence through Git will be disabled: {str(e)}")
        return False

def commit_and_push(message):
    """Commit all changes and push to remote"""
    try:
        # Add all changes
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Git add error: {result.stderr}")
            return False
        
        # Check if there are changes to commit
        try:
            status = subprocess.check_output(['git', 'status', '--porcelain'], stderr=subprocess.PIPE).decode('utf-8')
            if not status.strip():
                # No changes to commit
                return True
        except subprocess.CalledProcessError:
            print("Unable to check Git status, skipping commit")
            return False
        
        # Commit changes
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"{message} - Automated commit at {timestamp}"
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Git commit error: {result.stderr}")
            return False
        
        # Check if we have origin remote before trying to pull/push
        try:
            remotes = subprocess.check_output(['git', 'remote'], stderr=subprocess.PIPE).decode('utf-8').strip()
            if 'origin' not in remotes.split('\n'):
                print("No 'origin' remote found, skipping pull/push")
                return True  # Still return True since we committed locally
        except subprocess.CalledProcessError:
            print("Unable to check Git remotes, skipping pull/push")
            return True  # Still return True since we committed locally
        
        # Pull latest changes
        try:
            result = subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Git pull error: {result.stderr}")
                # Try to resolve simple conflicts
                subprocess.run(['git', 'checkout', '--theirs', '.'], stderr=subprocess.PIPE)
                subprocess.run(['git', 'add', '.'], stderr=subprocess.PIPE)
                subprocess.run(['git', 'rebase', '--continue'], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print("Git pull failed, continuing with local commit only")
        
        # Push changes to remote
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                
                print(f"Git push error (attempt {attempt+1}/{max_attempts}): {result.stderr}")
                if attempt < max_attempts - 1:
                    # Wait before retry
                    time.sleep(3)
            except subprocess.CalledProcessError:
                print(f"Git push failed (attempt {attempt+1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    time.sleep(3)
        
        print("All push attempts failed, but changes are committed locally")
        return True  # Return True since we at least committed locally
    except Exception as e:
        print(f"Error in Git operations: {str(e)}")
        return False 