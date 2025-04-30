# Fix for "Repository Not Found" Error

The error you're seeing (`repository 'https://github.com/perisri101/AwaazTimetable.git/' not found`) indicates that your AwaazTimetable app is trying to push data to a GitHub repository that doesn't exist.

## Option 1: Create the Repository on GitHub

1. Go to GitHub (https://github.com)
2. Log in with your GitHub account (username: perisri101)
3. Click on the "+" icon in the top-right corner and select "New repository"
4. Enter "AwaazTimetable" as the repository name
5. Choose visibility (Public or Private)
6. Initialize with a README (optional)
7. Click "Create repository"

## Option 2: Use a Different Existing Repository

If you want to use a different repository instead:

1. Run the `update_git_remote.py` script to update the remote URL:

```bash
python update_git_remote.py --url https://github.com/your-username/your-repo.git --username your-username --token your-personal-access-token
```

## Configure Render.com (Required for both options)

After you've created or selected your repository, you need to set these environment variables on Render.com:

1. Go to the Render Dashboard
2. Select your AwaazTimetable service
3. Go to the "Environment" tab
4. Add these environment variables:
   - `GIT_REPO_URL`: Your repository URL (e.g., `https://github.com/perisri101/AwaazTimetable.git`)
   - `GIT_USERNAME`: Your GitHub username (e.g., `perisri101`)
   - `GIT_TOKEN`: A GitHub Personal Access Token with `repo` scope
5. Click "Save Changes" and redeploy your service

## Creating a GitHub Personal Access Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "AwaazTimetable App"
4. Set an expiration date
5. Select the `repo` scope
6. Click "Generate token"
7. Copy the token immediately (you won't be able to see it again)

## Testing Your Connection

Once you've set up your repository and environment variables, run:

```bash
python test_git_connection.py
```

This will test if your application can connect to and push to the repository. 