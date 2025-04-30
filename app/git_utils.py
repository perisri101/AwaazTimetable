import os
import subprocess
import time
from datetime import datetime

def setup_git_credentials(repo_path):
    """Setup git credentials for automated commits"""
    email = os.environ.get('GIT_EMAIL', 'app@awaaz-timetable.com')
    name = os.environ.get('GIT_USERNAME', 'Awaaz Timetable App')
    
    os.chdir(repo_path)
    subprocess.run(['git', 'config', 'user.email', email])
    subprocess.run(['git', 'config', 'user.name', name])
    
    # If using GitHub token for authentication
    if 'GIT_TOKEN' in os.environ and 'GIT_USERNAME' in os.environ:
        token = os.environ.get('GIT_TOKEN')
        username = os.environ.get('GIT_USERNAME')
        repo_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8').strip()
        
        # Change HTTPS URL to include authentication
        if repo_url.startswith('https://'):
            authenticated_url = f'https://{username}:{token}@' + repo_url[8:]
            subprocess.run(['git', 'remote', 'set-url', 'origin', authenticated_url])

def commit_and_push(message):
    """Commit all changes and push to remote"""
    # Add all changes
    result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git add error: {result.stderr}")
        return False
    
    # Check if there are changes to commit
    status = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
    if not status.strip():
        # No changes to commit
        return True
    
    # Commit changes
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"{message} - Automated commit at {timestamp}"
    result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git commit error: {result.stderr}")
        return False
    
    # Pull latest changes
    result = subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git pull error: {result.stderr}")
        # Try to resolve simple conflicts
        subprocess.run(['git', 'checkout', '--theirs', '.'])
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'rebase', '--continue'])
    
    # Push changes to remote
    max_attempts = 3
    for attempt in range(max_attempts):
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        print(f"Git push error (attempt {attempt+1}/{max_attempts}): {result.stderr}")
        if attempt < max_attempts - 1:
            # Wait before retry
            time.sleep(3)
    
    return False 