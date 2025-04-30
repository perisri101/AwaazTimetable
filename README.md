# Awaaz Flexy Timetable

A flexible scheduling system for caregivers, allowing for 24/7 schedule templates, checklists, and calendar management.

## Features

- Create weekly schedule templates with 2-hour blocks
- Assign multiple caregivers to each time slot
- Configure checklists for each time slot with tasks
- Create calendars from templates for specific time periods
- View schedules by caregiver, hourly view, or summary
- Track caregiver hours with max 40 hrs/week, 8 hrs/day, 5 days/week limits
- Overtime calculation at 1.5x rate for hours above 40 per week
- Mobile-responsive design for access on any device
- Customizable shift durations
- Predefined activities/tasks for checklist creation
- Category-based organization of activity checklists

## Local Development

### Prerequisites
- Python 3.9+ (recommended: Python 3.9.18 as specified in runtime.txt)
- pip
- Git

### Setup
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AwaazTimetable.git
   cd AwaazTimetable
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```
   
   **Alternative running methods:**
   - If the above doesn't work, try running the main module directly:
     ```
     cd app
     python main.py
     ```
   - Or using the wsgi module:
     ```
     python wsgi.py
     ```

5. Access the application at http://localhost:5000

### Troubleshooting Common Issues

#### Python Version Compatibility
This application is designed to work with Python 3.9. If you're using a newer version (like Python 3.13+), you might encounter compatibility issues with SQLAlchemy. To fix this:

```pip install --upgrade sqlalchemy flask-sqlalchemy flask-login flask-wtf
```

#### Import Errors
If you encounter import errors related to modules like 'forms' or 'models', check that you're running the application from the correct directory:

```python
# Correct the import statements in app/main.py
from .models import db, User, Caregiver, Template, Calendar, Shift, ChecklistItem, ActivityCategory, Activity
from .forms import LoginForm, UserForm, CaregiverForm, TemplateForm
```

#### Password Hash Compatibility Error
If you encounter a `ValueError: unsupported hash type scrypt:32768:8:1` error on Render.com or another hosting platform, this is due to a hash algorithm incompatibility. To fix this:

1. Modify the User model to use a more compatible hashing algorithm (already implemented in this repository):
   ```python
   def set_password(self, password):
       self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
   ```

2. For existing databases with users, run the password upgrade script:
   ```
   cd app
   python upgrade_passwords.py
   ```

3. Update your requirements.txt to pin Werkzeug to a compatible version (if needed):
   ```
   Werkzeug==2.0.3
   Flask==2.0.3
   ```

4. Make sure your Render.com environment has the correct Python version:
   - Add `PYTHON_VERSION=3.9.18` to your environment variables

#### Database Issues
If you encounter database errors:

```
python app/fix_db.py
```

This will ensure necessary columns exist in your database schema.

## Deployment

The application is ready for deployment to cloud platforms like Render, Heroku, or PythonAnywhere.

### Deploying to Render.com

1. **Create a Render.com account**
   - Sign up at [render.com](https://render.com/) if you don't have an account

2. **Connect your GitHub repository**
   - In your Render dashboard, go to the "Blueprints" section
   - Click "New Blueprint Instance"
   - Connect your GitHub account and select your repository

3. **Create a new Web Service**
   - Click on "New Web Service" in your dashboard
   - Connect your GitHub repository
   - Choose "Python" as the environment

4. **Configure your service**
   - **Name**: Choose a name for your service (e.g., awaaz-timetable)
   - **Environment**: Python 3.9
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your preferred branch)
   - **Build Command**: `pip install -r requirements.txt && python fix_render.py`
   - **Start Command**: `gunicorn 'app:create_app()'`
   - **Instance Type**: Free (for development) or Basic (for production)

5. **Set Environment Variables**
   - Scroll down to the "Environment Variables" section and add:
     - `SECRET_KEY`: A secure random string (e.g., generate one using `openssl rand -hex 24`)
     - `PYTHON_VERSION`: 3.9.18
     - `DATABASE_URL`: (Optional) If using PostgreSQL, add your database connection string

6. **Create Database (Optional)**
   - For a production environment, you may want to use PostgreSQL instead of SQLite
   - Create a PostgreSQL database in Render.com
   - Connect it to your web service using the `DATABASE_URL` environment variable

7. **Deploy your application**
   - Click "Create Web Service"
   - Render will build and deploy your application

8. **Access your deployed application**
   - Once deployment is complete, click on the URL provided by Render
   - You can also set up a custom domain in the settings

### Custom Domain Setup on Render.com (Optional)

1. Go to your Web Service in Render
2. Navigate to the "Settings" tab
3. Scroll to "Custom Domain"
4. Add your domain and follow the instructions to configure DNS settings

### Deploying to Heroku

1. Install the Heroku CLI
2. Login to Heroku:
   ```
   heroku login
   ```
3. Create a new Heroku app:
   ```
   heroku create awaaz-timetable
   ```
4. Add a PostgreSQL database:
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```
5. Deploy the application:
   ```
   git push heroku main
   ```
6. Open the application:
   ```
   heroku open
   ```

## Default Access

The application now runs without login requirements. All features are accessible directly from the dashboard.

The User authentication system has been removed to simplify deployment and avoid compatibility issues with password hashing on different platforms.

## Tech Stack

- **Backend**: Python with Flask
- **Database**: SQLAlchemy with SQLite (development) or PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Containerization**: Docker (optional)

## Project Structure

```
AwaazFlexyTimetable/
├── app/                    # Application code
│   ├── templates/          # HTML templates
│   │   ├── calendars/      # Calendar-related templates
│   │   └── templates/      # Template-related templates
│   ├── main.py             # Main Flask application
│   ├── models.py           # Database models
│   ├── forms.py            # Form definitions
│   └── fix_db.py           # Database migration helper
├── app.py                  # Application entry point
├── wsgi.py                 # WSGI entry point for production servers
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version for deployment
├── Procfile                # Heroku configuration
└── README.md               # Project documentation
```

## Usage Guide

### Creating Templates

1. Log in to the system
2. Navigate to "Templates" and create a new template
3. Assign caregivers to time slots
4. Add checklist items for tasks to be completed during each time slot
5. Save the template

### Creating Calendars

1. Navigate to "Calendars" and create a new calendar
2. Select a template to base the calendar on
3. Select a start date
4. The calendar will be created with the shifts and checklist items from the template

### Managing Caregivers

1. Administrators can manage caregivers from the "Manage Caregivers" section
2. Add new caregivers with their work hour limitations and hourly rates
3. Edit or delete existing caregivers

### Managing Activities

1. Administrators can manage activity categories and activities
2. Create categories to organize related activities
3. Add activities with descriptions within each category
4. Use activities when creating checklist items in templates

### Viewing Reports

1. Navigate to a calendar
2. Click the "Reports" button
3. View various metrics and analytics, including:
   - Caregiver hours and status
   - Coverage heatmap
   - Cost calculations including overtime
   - Summary statistics
   - Daily distribution

### Managing Checklist Items

1. Checklist items can be created when setting up templates
2. Each 2-hour time slot can have multiple checklist items
3. When a template is used to create a calendar, the checklist items are copied
4. In calendar view, checklist items can be toggled (marked as complete/incomplete)

#### Implementing the Checklist Toggle Functionality

The frontend already contains a `toggleChecklistItem()` function in the calendar view (app/templates/calendars/view.html). To make this function work:

1. Add an API endpoint in app/main.py:

```python
@app.route('/api/calendars/checklist/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_checklist_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    
    # Toggle the completion status
    item.completed = not item.completed
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': item.to_dict()
    })
```

2. Update the `toggleChecklistItem()` function in app/templates/calendars/view.html to call this endpoint:

```javascript
// Toggle checklist item completion
function toggleChecklistItem(itemId, completed) {
    // Update local data
    const item = calendarData.checklists.find(item => item.id === itemId);
    if (item) {
        item.completed = completed;
    }
    
    // Send update to server
    fetch(`/api/calendars/checklist/${itemId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error toggling checklist item:', data);
            // Revert UI if there was an error
            if (item) {
                item.completed = !completed;
                const checkbox = document.querySelector(`.checklist-toggle[data-item-id="${itemId}"]`);
                if (checkbox) checkbox.checked = !completed;
            }
        }
    })
    .catch(error => {
        console.error('Error toggling checklist item:', error);
    });
}
```

3. Make sure you have a CSRF token meta tag in your base template:

```html
<!-- Add this to your base.html head section -->
<meta name="csrf-token" content="{{ csrf_token() }}">
```

## Development with Docker

To run the application using Docker:

1. Make sure Docker and Docker Compose are installed
2. Run the application:
   ```bash
   docker-compose up
   ```
3. The application will be available at http://localhost:5000
4. The application will reload automatically when changes are made to the code

## License

This project is licensed under the MIT License. 