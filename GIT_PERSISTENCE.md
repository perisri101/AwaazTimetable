# Git-Based Persistence System for AwaazTimetable

## Overview

AwaazTimetable uses an innovative Git-based data persistence system that ensures your data is safely stored and versioned, especially when deployed on stateless platforms like Render.com where traditional database storage might be lost between container restarts.

## How It Works

### Data Storage Architecture

1. **JSON File Storage**: All application data is stored as structured JSON files in the `data/` directory:
   - `data/meta.json`: Stores metadata like ID sequences
   - `data/caregivers/*.json`: One file per caregiver
   - `data/templates/*.json`: One file per schedule template
   - `data/calendars/*.json`: One file per calendar
   - `data/shifts/*.json`: Shift assignments by template/calendar
   - `data/checklists/*.json`: Checklist items by template/calendar
   - `data/activities/*.json`: Activity definitions
   - `data/activity_categories/*.json`: Activity category definitions

2. **Git Version Control**: Each change to any data file is automatically committed to a local Git repository. This happens through the `_safe_commit()` function in `gitdb.py` which is called after every data-changing operation.

3. **Remote Backups**: Commits are automatically pushed to a remote GitHub repository, ensuring data persists between container restarts on platforms like Render.com.

4. **Automatic Recovery**: When the application starts, it automatically sets up the Git repository and ensures it's properly configured to pull and push changes.

### Data Flow

1. **User Interaction**: A user makes a change through the web interface (e.g., creates a new caregiver)
2. **API Call**: Flask routes handle the request and call appropriate functions in `gitdb.py`
3. **Data Storage**: The data is saved as JSON in the appropriate directory
4. **Git Commit**: The `_safe_commit()` function in `gitdb.py` is called to commit changes
5. **Git Push**: Changes are pushed to the remote repository via `git_utils.py`

## Key Components

### 1. gitdb.py

The heart of the persistence system, this module:
- Implements CRUD operations for all entity types (caregivers, templates, calendars, etc.)
- Saves data as JSON files in the appropriate directory
- Calls `_safe_commit()` after data-changing operations
- Provides abstraction so the rest of the application doesn't need to deal with Git directly

Key functions:
- `_get_meta()`: Retrieves metadata like next ID sequences
- `_save_meta()`: Updates metadata
- `_get_next_id()`: Gets the next available ID for a given entity type
- `_save_entity()`: Saves an entity and commits the change
- `_safe_commit()`: Safely commits changes to Git

### 2. git_utils.py

Handles Git operations for the persistence system:
- Configures Git credentials
- Performs repository setup
- Manages commits and pushes
- Provides diagnostic tools

Key functions:
- `setup_git_credentials()`: Configures Git authentication
- `commit_and_push()`: Commits changes and pushes to remote
- `run_git_diagnostic()`: Runs diagnostics on the Git repository

### 3. setup_render_repo.py

Initializes the Git repository for Render.com deployment:
- Creates and initializes a local Git repository if needed
- Sets up Git user configuration
- Configures remote repository settings
- Ensures the data directory is tracked

Key functions:
- `setup_local_repo()`: Sets up a local Git repository
- `run_git_diagnostic()`: Runs diagnostics on the Git repository

## Benefits of Git-Based Persistence

1. **Stateless Deployment Compatibility**: Perfect for platforms like Render.com where container storage is ephemeral
2. **Version History**: Complete history of all data changes
3. **Disaster Recovery**: Easy restoration from any point in history
4. **Transparent Data Storage**: Human-readable JSON files instead of opaque database files
5. **No Database Dependencies**: No need for external database services
6. **Simple Backup and Migration**: Clone the repository to back up or migrate all data
7. **Offline Capability**: Commits work even when remote push fails

## Setup Guide

### Prerequisites

- Git installed and configured on your system
- GitHub account with a repository for the application
- GitHub personal access token with the `repo` scope

### Environment Variables

The Git persistence system requires these environment variables:

- `GIT_REPO_URL`: URL of your GitHub repository (e.g., `https://github.com/username/AwaazTimetable.git`)
- `GIT_USERNAME`: Your GitHub username
- `GIT_TOKEN`: A GitHub personal access token with `repo` permissions
- `GIT_EMAIL` (optional): Email to use for Git commits (defaults to `app@awaaz-timetable.com`)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AwaazTimetable.git
   cd AwaazTimetable
   ```

2. Set up environment variables:
   ```bash
   # For bash/zsh
   export GIT_REPO_URL="https://github.com/yourusername/AwaazTimetable.git"
   export GIT_USERNAME="yourusername"
   export GIT_TOKEN="your_personal_access_token"
   
   # For Windows CMD
   set GIT_REPO_URL=https://github.com/yourusername/AwaazTimetable.git
   set GIT_USERNAME=yourusername
   set GIT_TOKEN=your_personal_access_token
   ```

3. Run the health check script to verify your setup:
   ```bash
   python git_health_check.py
   ```

### Render.com Deployment

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Add the required environment variables:
   - `GIT_REPO_URL`: Your GitHub repository URL
   - `GIT_USERNAME`: Your GitHub username
   - `GIT_TOKEN`: Your GitHub personal access token
   - `SECRET_KEY`: A random string for Flask session security

## Troubleshooting

### Health Check Script

Run the comprehensive health check script to diagnose and fix issues:

```bash
python git_health_check.py
```

For automatic fixes:

```bash
python git_health_check.py --fix
```

### Common Issues

1. **"Repository not found" error**:
   - Ensure the repository exists on GitHub
   - Verify your GitHub username and token are correct
   - Check that environment variables are set correctly

2. **"Push failed" error**:
   - Ensure your token has the correct permissions
   - Check if there are conflicts between local and remote repositories
   - Try manually pushing with `--force` if necessary

3. **"Authentication failed" error**:
   - Verify your GitHub username and token are correct
   - Ensure the token has not expired
   - Check that you have proper permissions to the repository

4. **No commits showing on GitHub**:
   - Check that environment variables are properly set
   - Run `python debug_git_operations.py --test-push` to test pushing
   - Check if the authentication is working correctly

### Manual Diagnostics

For detailed diagnostics, run the monitoring script:

```bash
python debug_git_operations.py --monitor
```

This will show real-time Git operations and help you identify issues.

## Maintenance and Backup

### Regular Maintenance

1. Periodically check the GitHub repository to ensure data is being properly pushed
2. Run the health check script occasionally to ensure everything is working:
   ```bash
   python git_health_check.py
   ```

3. Rotate your GitHub token periodically for security

### Backup and Recovery

To back up your data:

1. Clone the repository to a local machine:
   ```bash
   git clone https://github.com/yourusername/AwaazTimetable.git backup-awaaz
   ```

2. Keep a backup of the `data/` directory separately if needed

To recover data:

1. Ensure the repository is properly set up with the correct environment variables
2. Run the application - it will automatically pull the latest data from the repository

## Implementation Details

### Automatic Commit Strategy

The system automatically commits changes:

1. Each data-modifying operation calls `_safe_commit()` in `gitdb.py`
2. `_safe_commit()` checks if Git persistence is enabled
3. If enabled, it calls `commit_and_push()` in `git_utils.py`
4. `commit_and_push()` adds all changes, commits with the provided message, and pushes to remote

### Conflict Resolution

The system handles common Git conflicts:

1. If a push fails due to a conflict, it attempts to resolve by:
   - Trying to pull changes first
   - Retrying the push
   - Logging the conflict for manual resolution if needed

### Error Handling

Robust error handling ensures the application keeps working even if Git operations fail:

1. All Git operations are wrapped in try/except blocks
2. Detailed error messages are logged
3. The application continues functioning even if Git operations fail

## Advanced Configuration

### Custom Repository Structure

To use a different directory structure:

1. Modify the `DATA_DIR` constant in `gitdb.py`
2. Update the entity-specific functions to use your preferred paths

### Multiple Remotes

To push to multiple remote repositories:

1. Configure additional remotes in Git:
   ```bash
   git remote add backup https://github.com/yourusername/AwaazTimetable-backup.git
   ```

2. Modify `git_utils.py` to push to multiple remotes

## Security Considerations

1. **GitHub Token Protection**: The GitHub token should be kept secure and never committed to the repository
2. **Data Privacy**: Consider repository visibility (public vs. private) based on your data sensitivity
3. **Access Control**: Carefully manage who has access to the GitHub repository
4. **Regular Token Rotation**: Periodically rotate your GitHub tokens

## Performance Considerations

For larger deployments:

1. **Commit Frequency**: Batch related changes to reduce the number of commits
2. **Repository Size**: Regularly monitor your repository size
3. **Large Files**: Avoid storing large files (images, etc.) in the data directory 