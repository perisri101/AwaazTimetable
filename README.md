# Awaaz Flexy Timetable

A flexible 24/7 scheduling system for caregivers built with Python, Flask, and Docker.

## Features

- Create weekly schedule templates with 2-hour time blocks
- Assign multiple caregivers to each time slot
- Configure checklist items for each time slot
- Generate calendars from templates
- View schedules by caregiver or in hourly view
- Track caregiver hours with limits (40 hrs/week, 8 hrs/day, 5 days/week)
- Generate reports and analytics
- Multi-user system with admin capabilities

## Tech Stack

- **Backend**: Python 3.11 with Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Containerization**: Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AwaazFlexyTimetable.git
cd AwaazFlexyTimetable
```

2. Build and start the application using Docker Compose:
```bash
docker-compose up -d --build
```

3. Access the application at [http://localhost:5000](http://localhost:5000)

### Default Credentials

The application comes with a default admin account:
- Username: admin
- Password: admin

*Please change these credentials in a production environment.*

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