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
- Python 3.9+
- pip

### Setup
1. Clone the repository
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
5. Access the application at http://localhost:5000

## Deployment

The application is ready for deployment to cloud platforms like Render, Heroku, or PythonAnywhere.

### Deploying to Render

1. Create a new Web Service in your Render dashboard
2. Connect your GitHub repository
3. Use the following settings:
   - **Environment**: Python 3.9
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn 'app:create_app()'`
4. Add the following environment variables:
   - `SECRET_KEY`: A secure random string
   - `DATABASE_URL`: (Optional) PostgreSQL connection string if using a database service

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

## Default Login

- Username: admin
- Password: admin

*Note: Change the default login credentials immediately after first login for security reasons.*

## Tech Stack

- **Backend**: Python 3.11 with Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Containerization**: Docker

## Project Structure

```
AwaazFlexyTimetable/
├── app/                    # Application code
│   ├── templates/          # HTML templates
│   │   ├── calendars/      # Calendar-related templates
│   │   └── templates/      # Template-related templates
│   ├── main.py             # Main Flask application
│   ├── models.py           # Database models
│   └── forms.py            # Form definitions
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
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
2. Add new caregivers with their work hour limitations
3. Edit or delete existing caregivers

### Viewing Reports

1. Navigate to a calendar
2. Click the "Reports" button
3. View various metrics and analytics, including:
   - Caregiver hours and status
   - Coverage heatmap
   - Summary statistics
   - Daily distribution

## Development

To run the application in development mode:

```bash
docker-compose up
```

The application will reload automatically when changes are made to the code.

## License

This project is licensed under the MIT License. 