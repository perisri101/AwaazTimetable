# AwaazTimetable

A flexible 24/7 scheduling system for caregivers with Git-based data persistence.

![AwaazTimetable Dashboard](https://placehold.co/600x400/3f51b5/white?text=AwaazTimetable+Dashboard)

## Overview

AwaazTimetable is a comprehensive scheduling application designed specifically for caregiving organizations. It allows administrators to create weekly schedule templates, assign caregivers to time slots, configure checklists for each shift, and generate calendars from templates for specific time periods.

### Key Features

- Create weekly schedule templates with 2-hour blocks
- Assign multiple caregivers to each time slot
- Configure checklists for each time slot with tasks
- Create calendars from templates for specific time periods
- View schedules by caregiver, hourly view, or summary
- Track caregiver hours with max 40 hrs/week, 8 hrs/day, 5 days/week limits
- Overtime calculation at 1.5x rate for hours above 40 per week
- Mobile-responsive design for access on any device
- Customizable shift durations (2-hour blocks or custom lengths)
- Real-time availability tracking for caregivers
- Conflict detection when scheduling overlapping shifts
- Dashboard with schedule overview and alerts
- Reporting tools for hours worked and schedule adherence
- Template preview functionality with multiple views for iterative refinement
- Master list of predefined activities/tasks for checklist creation
- Category-based organization of activity checklists by groups

## Git-Based Data Persistence

AwaazTimetable uses an innovative Git-based data persistence system that ensures your data is safely stored and versioned, even when deployed on stateless platforms like Render.com.

### How It Works

1. **JSON File Storage**: All data (caregivers, templates, schedules, etc.) is stored as JSON files in the `data/` directory.
2. **Git Version Control**: Each change to the data is automatically committed to a local Git repository.
3. **Remote Backups**: Changes are pushed to a remote GitHub repository, ensuring data persists between container restarts.
4. **Automatic Recovery**: On application startup, the latest data is pulled from the remote repository.

### Benefits of Git-Based Persistence

- **Stateless Deployment**: Perfect for container-based platforms like Render.com
- **Version History**: Complete history of all data changes
- **Disaster Recovery**: Easy restoration from any point in history
- **Transparent Data**: Human-readable JSON files instead of opaque database files
- **No Database Dependencies**: No need for external database services

## Installation

### Prerequisites

- Python 3.9+
- Git installed and configured
- GitHub account (for remote repository)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AwaazTimetable.git
   cd AwaazTimetable
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the health check script to ensure your environment is set up correctly:
   ```bash
   python git_health_check.py --fix
   ```

5. Set up necessary environment variables:
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

6. Run the application:
   ```bash
   python app.py
   ```

7. Access the application at `http://localhost:8000`

## Deployment on Render.com

AwaazTimetable is designed to work seamlessly on Render.com's free tier, using Git for data persistence.

### Setup Instructions

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Configure the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn 'app:create_app()'`
4. Add the following environment variables:
   - `GIT_REPO_URL`: Your GitHub repository URL
   - `GIT_USERNAME`: Your GitHub username
   - `GIT_TOKEN`: A GitHub personal access token with `repo` scope
   - `SECRET_KEY`: A random string for Flask session security

### Creating a GitHub Personal Access Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "AwaazTimetable App"
4. Set an expiration date
5. Select the `repo` scope
6. Click "Generate token"
7. Copy the token immediately (you won't be able to see it again)

## Git Persistence Troubleshooting

If you encounter issues with the Git-based persistence system, use these diagnostic tools:

### Health Check

Run the comprehensive health check script:

```bash
python git_health_check.py
```

To automatically fix issues:

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

3. **"Authentication failed" error**:
   - Verify your GitHub username and token
   - Ensure the token hasn't expired

## Project Structure

```
AwaazTimetable/
├── app/                        # Main application package
│   ├── __init__.py            # Package initializer
│   ├── main.py                # Flask application logic
│   ├── models.py              # SQLAlchemy model definitions
│   ├── forms.py               # Flask-WTF form definitions
│   ├── gitdb.py               # Git-based database functionality
│   ├── git_utils.py           # Git utility functions
│   ├── setup_render_repo.py   # Repository setup for Render.com
│   └── templates/             # Jinja2 HTML templates
├── data/                      # Data directory (JSON files)
│   ├── meta.json              # Metadata for IDs
│   ├── caregivers/            # Caregiver JSON files
│   ├── templates/             # Template JSON files
│   ├── calendars/             # Calendar JSON files
│   ├── shifts/                # Shift assignment files
│   ├── checklists/            # Checklist item files
│   ├── activities/            # Activity JSON files
│   └── activity_categories/   # Activity category files
├── git_health_check.py        # Health check and fix script
├── test_git_connection.py     # Connection test script
├── app.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── Procfile                   # Render.com deployment config
└── runtime.txt                # Python version specification
```

## Data Structure

The application stores all data as JSON files in the `data/` directory:

- **meta.json**: Stores metadata including ID counters
- **caregivers/*.json**: One file per caregiver
- **templates/*.json**: One file per schedule template
- **calendars/*.json**: One file per generated calendar
- **shifts/*.json**: Shift assignments by template/calendar
- **checklists/*.json**: Checklist items by template/calendar
- **activities/*.json**: Activity definitions
- **activity_categories/*.json**: Activity category definitions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you need help with AwaazTimetable, please create an issue in the GitHub repository. 