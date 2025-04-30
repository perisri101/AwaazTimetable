from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta, date
import os
import json
import calendar
from .models import db, User, Caregiver, Template, Calendar, Shift, ChecklistItem, ActivityCategory, Activity
from .forms import TemplateForm, CaregiverForm
from . import gitdb  # Import our new GitDB module
import os.path

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-awaaz-flexy-timetable')

# Use environment variable for database URL or default to SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Heroku Postgres uses 'postgres://' but SQLAlchemy expects 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///scheduler.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

# Initialize Git credentials for the repository
@app.before_first_request
def setup_git():
    try:
        print("\n==== SETTING UP GIT-BASED DATABASE PERSISTENCE ====")
        
        # First ensure we have a local repository set up
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_render_repo", 
                                                         os.path.join(os.path.dirname(__file__), "setup_render_repo.py"))
            setup_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup_module)
            
            # Set up the repository
            setup_module.setup_local_repo()
            print("Local Git repository setup completed")
            
            # Run diagnostics for extra information
            print("\n==== GIT REPOSITORY DIAGNOSTIC REPORT ====")
            setup_module.run_git_diagnostic()
            print("==== END DIAGNOSTIC REPORT ====\n")
        except Exception as e:
            print(f"Warning: Could not set up local Git repository: {str(e)}")
        
        # Now set up Git credentials
        from .git_utils import setup_git_credentials
        repo_path = os.path.dirname(os.path.dirname(__file__))
        git_available = setup_git_credentials(repo_path)
        app.config['GIT_PERSISTENCE_ENABLED'] = git_available
        
        if not git_available:
            print("\n==== WARNING: GIT PERSISTENCE DISABLED ====")
            print("Git persistence is disabled. Data will only be stored locally.")
            print("Local data will NOT be automatically committed and pushed to Git.")
            print("This means data may be lost if the application container is restarted.")
            print("Check the logs above for more information on what went wrong.")
            print("===============================================\n")
        else:
            print("\n==== GIT PERSISTENCE ENABLED ====")
            print("Git persistence is enabled and working.")
            print("Changes to data will be automatically committed to the Git repository.")
            print("You can see the Git operations in the logs with [GitDB] prefix.")
            print("====================================\n")
    except Exception as e:
        app.config['GIT_PERSISTENCE_ENABLED'] = False
        print(f"\n==== ERROR SETTING UP GIT: {str(e)} ====")
        print("WARNING: Git persistence is disabled, data will only be stored locally")
        print("This means your data may be lost if the application container is restarted.")
        print("==========================================\n")

# Initialize database
def create_tables():
    with app.app_context():
        # Check if we need to add columns to existing database
        import sqlite3
        import os
        
        db_path = 'instance/scheduler.db'
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if rate column exists in caregiver table
                cursor.execute("PRAGMA table_info(caregiver)")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                
                if 'rate' not in column_names:
                    print("Adding rate column to caregiver table...")
                    cursor.execute("ALTER TABLE caregiver ADD COLUMN rate FLOAT DEFAULT 0.0")
                    conn.commit()
                    print("Rate column added successfully!")
                
                # Check if activity_id column exists in checklist_item table
                cursor.execute("PRAGMA table_info(checklist_item)")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                
                if 'activity_id' not in column_names:
                    print("Adding activity_id column to checklist_item table...")
                    cursor.execute("ALTER TABLE checklist_item ADD COLUMN activity_id INTEGER")
                    conn.commit()
                    print("activity_id column added successfully!")
                
                conn.close()
            except Exception as e:
                print(f"Error checking/adding columns: {str(e)}")
                # If we can't modify the existing table, recreate the database
                try:
                    os.remove(db_path)
                    print("Removed corrupted database file. Will recreate.")
                except:
                    pass
        
        # Create tables
        db.create_all()

# Call the function to initialize the database
create_tables()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    templates = gitdb.get_all_templates()
    calendars = gitdb.get_all_calendars()
    
    # Create a dictionary of templates for easy lookup
    templates_dict = {template['id']: template for template in templates}
    
    # Enrich calendars with template names
    for calendar in calendars:
        template_id = calendar.get('template_id')
        if template_id and template_id in templates_dict:
            calendar['template_name'] = templates_dict[template_id]['name']
        else:
            calendar['template_name'] = f"Unknown (ID: {template_id})"
    
    return render_template('dashboard.html', templates=templates, calendars=calendars)

# Management routes for admins
@app.route('/manage/caregivers')
def manage_caregivers():
    caregivers = gitdb.get_all_caregivers()
    form = CaregiverForm()
    return render_template('manage_caregivers.html', caregivers=caregivers, form=form)

@app.route('/manage/caregivers/add', methods=['POST'])
def add_caregiver():
    # Get JSON data instead of form data
    data = request.json
    
    # Manual validation
    errors = {}
    if not data.get('name'):
        errors['name'] = ['Name is required']
    elif len(data.get('name')) < 3:
        errors['name'] = ['Name must be at least 3 characters']
    
    if not data.get('email'):
        errors['email'] = ['Email is required']
    # Simple email validation
    elif '@' not in data.get('email'):
        errors['email'] = ['Invalid email format']
    
    # Check if email already exists
    existing_caregivers = gitdb.get_all_caregivers()
    if not errors.get('email') and any(c['email'] == data.get('email') for c in existing_caregivers):
        errors['email'] = ['Email already in use']
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        rate_value = float(data.get('rate', 0)) if data.get('rate') else 0
        data['rate'] = rate_value
    except ValueError:
        errors['rate'] = ['Rate must be a valid number']
        return jsonify({'success': False, 'errors': errors}), 400
    
    # Create new caregiver
    caregiver = gitdb.create_caregiver(data)
    return jsonify({'success': True, 'caregiver': caregiver})

@app.route('/manage/caregivers/edit/<int:id>', methods=['POST'])
def edit_caregiver(id):
    caregiver = gitdb.get_caregiver(id)
    
    if not caregiver:
        return jsonify({'success': False, 'message': 'Caregiver not found'}), 404
    
    # Get JSON data instead of form data
    data = request.json
    
    # Manual validation
    errors = {}
    if not data.get('name'):
        errors['name'] = ['Name is required']
    elif len(data.get('name')) < 3:
        errors['name'] = ['Name must be at least 3 characters']
    
    if not data.get('email'):
        errors['email'] = ['Email is required']
    # Simple email validation
    elif '@' not in data.get('email'):
        errors['email'] = ['Invalid email format']
    
    # Check if email already exists and it's not this caregiver's email
    existing_caregivers = gitdb.get_all_caregivers()
    for existing in existing_caregivers:
        if existing['email'] == data.get('email') and existing['id'] != id:
            errors['email'] = ['Email already in use']
            break
    
    try:
        rate_value = float(data.get('rate', 0)) if data.get('rate') else 0
        data['rate'] = rate_value
    except ValueError:
        errors['rate'] = ['Rate must be a valid number']
        return jsonify({'success': False, 'errors': errors}), 400
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    # Update caregiver
    updated_caregiver = gitdb.update_caregiver(id, data)
    return jsonify({'success': True, 'caregiver': updated_caregiver})

@app.route('/manage/caregivers/delete/<int:id>', methods=['POST'])
def delete_caregiver(id):
    success = gitdb.delete_caregiver(id)
    if not success:
        return jsonify({'success': False, 'message': 'Caregiver not found'}), 404
    
    return jsonify({'success': True})

# Template routes
@app.route('/templates')
def list_templates():
    templates = gitdb.get_all_templates()
    return render_template('templates/list.html', templates=templates)

@app.route('/templates/new', methods=['GET', 'POST'])
def new_template():
    if request.method == 'POST':
        template_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description', '')
        }
        
        gitdb.create_template(template_data)
        flash('Template created successfully', 'success')
        return redirect(url_for('list_templates'))
    
    form = TemplateForm()
    return render_template('templates/new.html', form=form)

@app.route('/templates/edit/<int:id>')
def edit_template(id):
    template = gitdb.get_template(id)
    if not template:
        flash('Template not found', 'danger')
        return redirect(url_for('list_templates'))
    
    caregivers = gitdb.get_all_caregivers()
    activities = gitdb.get_all_activities()
    return render_template('templates/edit.html', template=template, caregivers=caregivers, activities=activities)

@csrf.exempt
@app.route('/api/templates/<int:id>/shifts')
def get_template_shifts(id):
    try:
        # Get template shifts from gitdb
        shifts = gitdb.get_template_shifts(id)
        
        # Get template checklists from gitdb
        checklists = gitdb.get_template_checklists(id)
        
        # Create a structured response
        response = {
            'shifts': shifts if isinstance(shifts, list) else [],
            'checklists': checklists if isinstance(checklists, list) else []
        }
        
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error retrieving template data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving template data: {str(e)}',
            'shifts': [],
            'checklists': []
        }), 500

@csrf.exempt
@app.route('/api/templates/<int:id>/shifts', methods=['POST'])
def update_template_shifts(id):
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Get existing template
    template = gitdb.get_template(id)
    if not template:
        return jsonify({'success': False, 'message': 'Template not found'}), 404
    
    # Validate the data format
    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': 'Invalid data format. Expected JSON object'}), 400
    
    # Extract shifts and checklists arrays, ensuring they're properly formatted
    shifts = data.get('shifts', [])
    checklists = data.get('checklists', [])
    
    # Ensure shifts is an array
    if not isinstance(shifts, list):
        return jsonify({'success': False, 'message': 'Shifts must be an array'}), 400
    
    # Ensure checklists is an array
    if not isinstance(checklists, list):
        return jsonify({'success': False, 'message': 'Checklists must be an array'}), 400
    
    # Validate and clean up each shift object
    for i, shift in enumerate(shifts):
        # Ensure required fields exist and are integers
        if 'caregiver_id' not in shift:
            return jsonify({'success': False, 'message': f'Shift at index {i} is missing caregiver_id'}), 400
        
        if 'day_of_week' not in shift:
            return jsonify({'success': False, 'message': f'Shift at index {i} is missing day_of_week'}), 400
        
        if 'start_hour' not in shift:
            return jsonify({'success': False, 'message': f'Shift at index {i} is missing start_hour'}), 400
        
        if 'end_hour' not in shift:
            return jsonify({'success': False, 'message': f'Shift at index {i} is missing end_hour'}), 400
        
        # Convert to integers if they're not already
        try:
            shift['caregiver_id'] = int(shift['caregiver_id'])
            shift['day_of_week'] = int(shift['day_of_week'])
            shift['start_hour'] = int(shift['start_hour'])
            shift['end_hour'] = int(shift['end_hour'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': f'Shift at index {i} has invalid numeric values'}), 400
    
    # Validate and clean up each checklist item
    for i, item in enumerate(checklists):
        # Ensure required fields exist
        if 'description' not in item:
            return jsonify({'success': False, 'message': f'Checklist item at index {i} is missing description'}), 400
        
        if 'day_of_week' not in item:
            return jsonify({'success': False, 'message': f'Checklist item at index {i} is missing day_of_week'}), 400
        
        if 'start_hour' not in item:
            return jsonify({'success': False, 'message': f'Checklist item at index {i} is missing start_hour'}), 400
        
        if 'end_hour' not in item:
            return jsonify({'success': False, 'message': f'Checklist item at index {i} is missing end_hour'}), 400
        
        # Convert numeric fields to integers
        try:
            item['day_of_week'] = int(item['day_of_week'])
            item['start_hour'] = int(item['start_hour'])
            item['end_hour'] = int(item['end_hour'])
            
            # Convert activity_id to integer if present and not null
            if item.get('activity_id') is not None:
                item['activity_id'] = int(item['activity_id'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': f'Checklist item at index {i} has invalid numeric values'}), 400
        
        # Assign ID to new checklist items
        if not item.get('id'):
            item['id'] = gitdb._get_next_id('checklist_item')
    
    try:
        # Save template shifts and checklists
        gitdb.save_template_shifts(id, shifts)
        gitdb.save_template_checklists(id, checklists)
    except Exception as e:
        app.logger.error(f"Error saving template data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error saving template data: {str(e)}'
        }), 500
    
    return jsonify({
        'success': True, 
        'shifts_count': len(shifts),
        'checklists_count': len(checklists)
    })

@app.route('/templates/delete/<int:id>', methods=['POST'])
def delete_template(id):
    success = gitdb.delete_template(id)
    
    if not success:
        flash('Template not found or could not be deleted', 'danger')
    else:
        flash('Template deleted successfully', 'success')
    
    return redirect(url_for('list_templates'))

@app.route('/templates/preview/<int:id>')
def preview_template(id):
    template = gitdb.get_template(id)
    if not template:
        flash('Template not found', 'danger')
        return redirect(url_for('list_templates'))
    
    caregivers = gitdb.get_all_caregivers()
    return render_template('templates/preview.html', template=template, caregivers=caregivers)

@app.route('/api/templates/<int:id>/preview/caregiver/<int:caregiver_id>')
def preview_template_by_caregiver(id, caregiver_id):
    shifts = gitdb.get_template_shifts(id)
    
    # Filter shifts for this caregiver
    caregiver_shifts = [shift for shift in shifts if shift['caregiver_id'] == caregiver_id]
    
    return jsonify({
        'success': True,
        'shifts': caregiver_shifts
    })

@app.route('/api/templates/<int:id>/preview/day/<int:day>')
def preview_template_by_day(id, day):
    shifts = gitdb.get_template_shifts(id)
    checklists = gitdb.get_template_checklists(id)
    
    # Filter shifts for this day
    day_shifts = [shift for shift in shifts if shift['day_of_week'] == day]
    
    # Filter checklists for this day
    day_checklists = [item for item in checklists if item['day_of_week'] == day]
    
    # Group by hour
    hours = {}
    for hour in range(0, 24, 2):
        hours[hour] = {
            'shifts': [shift for shift in day_shifts if shift['start_hour'] <= hour < shift['end_hour']],
            'checklists': [item for item in day_checklists if item['start_hour'] <= hour < item['end_hour']]
        }
    
    return jsonify({
        'success': True,
        'day': day,
        'hours': hours
    })

@app.route('/api/templates/<int:id>/preview/hour/<int:hour>')
def preview_template_by_hour(id, hour):
    shifts = gitdb.get_template_shifts(id)
    checklists = gitdb.get_template_checklists(id)
    
    # Filter shifts for this hour across all days
    hour_shifts = [shift for shift in shifts if shift['start_hour'] <= hour < shift['end_hour']]
    
    # Filter checklists for this hour across all days
    hour_checklists = [item for item in checklists if item['start_hour'] <= hour < item['end_hour']]
    
    # Group by day
    days = {}
    for day in range(7):
        days[day] = {
            'shifts': [shift for shift in hour_shifts if shift['day_of_week'] == day],
            'checklists': [item for item in hour_checklists if item['day_of_week'] == day]
        }
    
    return jsonify({
        'success': True,
        'hour': hour,
        'days': days
    })

# Calendar routes
@app.route('/calendars')
def list_calendars():
    calendars = gitdb.get_all_calendars()
    templates = gitdb.get_all_templates()
    
    # Create a dictionary of templates for easy lookup
    templates_dict = {template['id']: template for template in templates}
    
    # Enrich calendars with template names
    for calendar in calendars:
        template_id = calendar.get('template_id')
        if template_id and template_id in templates_dict:
            calendar['template_name'] = templates_dict[template_id]['name']
        else:
            calendar['template_name'] = f"Unknown (ID: {template_id})"
            
    return render_template('calendars/list.html', calendars=calendars)

@app.route('/calendars/new')
def new_calendar():
    templates = gitdb.get_all_templates()
    return render_template('calendars/new.html', templates=templates)

@app.route('/api/calendars/create', methods=['POST'])
def create_calendar():
    data = request.json
    
    # Log received data for debugging
    app.logger.debug(f"Creating calendar with data: {data}")
    
    if not data.get('name'):
        app.logger.warning("Calendar creation failed: Name is required")
        return jsonify({'success': False, 'errors': {'name': ['Name is required']}}), 400
    
    if not data.get('template_id'):
        app.logger.warning("Calendar creation failed: Template is required")
        return jsonify({'success': False, 'errors': {'template_id': ['Template is required']}}), 400
    
    if not data.get('start_date'):
        app.logger.warning("Calendar creation failed: Start date is required")
        return jsonify({'success': False, 'errors': {'start_date': ['Start date is required']}}), 400
    
    # Check if template exists
    template = gitdb.get_template(data.get('template_id'))
    if not template:
        app.logger.warning(f"Calendar creation failed: Template {data.get('template_id')} not found")
        return jsonify({'success': False, 'errors': {'template_id': ['Template not found']}}), 400
    
    try:
        # Create calendar
        calendar = gitdb.create_calendar(data)
        
        app.logger.info(f"Calendar created successfully with ID {calendar['id']}")
        
        return jsonify({
            'success': True, 
            'calendar': calendar,
            'redirect': url_for('view_calendar', id=calendar['id'])
        })
    except Exception as e:
        app.logger.error(f"Error creating calendar: {str(e)}")
        return jsonify({'success': False, 'message': f"An error occurred: {str(e)}"}), 500

@app.route('/calendars/view/<int:id>')
def view_calendar(id):
    calendar = gitdb.get_calendar(id)
    if not calendar:
        flash('Calendar not found', 'danger')
        return redirect(url_for('list_calendars'))
    
    template_id = calendar.get('template_id')
    template = gitdb.get_template(template_id)
    
    # If template doesn't exist, create a placeholder
    if not template:
        template = {
            'id': template_id,
            'name': f"Unknown Template (ID: {template_id})",
            'description': "This template no longer exists."
        }
    
    caregivers = gitdb.get_all_caregivers()
    return render_template('calendars/view.html', calendar=calendar, template=template, caregivers=caregivers)

@app.route('/api/calendars/<int:id>/shifts')
def get_calendar_shifts(id):
    shifts = gitdb.get_calendar_shifts(id)
    checklists = gitdb.get_calendar_checklists(id)
    
    return jsonify({
        'shifts': shifts,
        'checklists': checklists
    })

@app.route('/api/calendars/checklist/<int:item_id>/toggle', methods=['POST'])
def toggle_checklist_item(item_id):
    item = gitdb.toggle_checklist_item(item_id)
    
    if not item:
        return jsonify({
            'success': False,
            'message': 'Checklist item not found'
        }), 404
    
    return jsonify({
        'success': True,
        'item': item
    })

@app.route('/calendars/reports/<int:id>')
def calendar_reports(id):
    calendar = gitdb.get_calendar(id)
    if not calendar:
        flash('Calendar not found', 'danger')
        return redirect(url_for('list_calendars'))
    
    # Get template information
    template_id = calendar.get('template_id')
    template = gitdb.get_template(template_id)
    
    if template:
        calendar['template_name'] = template['name']
    else:
        calendar['template_name'] = f"Unknown Template (ID: {template_id})"
        
    return render_template('calendars/reports.html', calendar=calendar)

@app.route('/api/calendars/<int:id>/reports')
def get_calendar_reports(id):
    calendar = gitdb.get_calendar(id)
    if not calendar:
        return jsonify({'success': False, 'message': 'Calendar not found'}), 404
        
    shifts = gitdb.get_calendar_shifts(id)
    
    # Calculate hours by caregiver
    caregiver_hours = {}
    total_cost = 0
    
    # Get all caregivers
    caregivers = gitdb.get_all_caregivers()
    caregivers_by_id = {c['id']: c for c in caregivers}
    
    # First pass: collect all hours
    for shift in shifts:
        caregiver_id = shift['caregiver_id']
        hours = shift['end_hour'] - shift['start_hour']
        
        if caregiver_id not in caregiver_hours:
            caregiver = caregivers_by_id.get(caregiver_id, {'name': 'Unknown', 'rate': 0})
            caregiver_hours[caregiver_id] = {
                'name': caregiver['name'],
                'total_hours': 0,
                'days': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'rate': caregiver.get('rate', 0),
                'overtime_hours': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'regular_hours': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'cost': 0
            }
        
        caregiver_hours[caregiver_id]['total_hours'] += hours
        caregiver_hours[caregiver_id]['days'][shift['day_of_week']] += hours
        
    # Second pass: calculate overtime and costs based on daily totals
    for caregiver_id, caregiver_data in caregiver_hours.items():
        # For each day, calculate regular and overtime hours
        for day in range(7):
            daily_hours = caregiver_data['days'][day]
            
            # First 10 hours are regular, rest are overtime
            regular_hours = min(10, daily_hours)
            overtime_hours = max(0, daily_hours - 10)
            
            caregiver_data['regular_hours'][day] = regular_hours
            caregiver_data['overtime_hours'][day] = overtime_hours
            
            # Calculate cost for this day
            regular_cost = regular_hours * caregiver_data['rate']
            overtime_cost = overtime_hours * (caregiver_data['rate'] * 1.5)
            day_cost = regular_cost + overtime_cost
            
            caregiver_data['cost'] += day_cost
            total_cost += day_cost
    
    # Calculate hours by day/time slot
    hours_by_time = {}
    for day in range(7):
        hours_by_time[day] = {}
        for hour in range(0, 24, 2):
            hours_by_time[day][hour] = {
                'caregivers': [],
                'count': 0
            }
    
    for shift in shifts:
        day = shift['day_of_week']
        caregiver_name = caregivers_by_id.get(shift['caregiver_id'], {'name': 'Unknown'})['name']
        for hour in range(shift['start_hour'], shift['end_hour'], 2):
            hours_by_time[day][hour]['caregivers'].append(caregiver_name)
            hours_by_time[day][hour]['count'] += 1
    
    return jsonify({
        'caregiver_hours': caregiver_hours,
        'hours_by_time': hours_by_time,
        'total_cost': total_cost
    })

@app.route('/calendars/delete/<int:id>', methods=['POST'])
def delete_calendar(id):
    success = gitdb.delete_calendar(id)
    if not success:
        flash('Calendar not found or could not be deleted', 'danger')
    else:
        flash('Calendar deleted successfully', 'success')
    
    return redirect(url_for('list_calendars'))

# Activity Category Management
@app.route('/manage/activity-categories')
def manage_activity_categories():
    categories = gitdb.get_all_activity_categories()
    return render_template('manage_activity_categories.html', categories=categories)

@app.route('/api/activity-categories', methods=['GET'])
def get_activity_categories():
    categories = gitdb.get_all_activity_categories()
    return jsonify({
        'success': True, 
        'categories': categories
    })

@app.route('/api/activity-categories', methods=['POST'])
def add_activity_category():
    data = request.json
    
    if not data.get('name'):
        return jsonify({'success': False, 'errors': {'name': ['Name is required']}}), 400
    
    category = gitdb.create_activity_category(data)
    
    return jsonify({'success': True, 'category': category})

@app.route('/api/activity-categories/<int:id>', methods=['PUT'])
def update_activity_category(id):
    category = gitdb.get_activity_category(id)
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
        
    data = request.json
    
    if not data.get('name'):
        return jsonify({'success': False, 'errors': {'name': ['Name is required']}}), 400
    
    updated_category = gitdb.update_activity_category(id, data)
    
    return jsonify({'success': True, 'category': updated_category})

@app.route('/api/activity-categories/<int:id>', methods=['DELETE'])
def delete_activity_category(id):
    # Check if category has activities
    activities = gitdb.get_activities_by_category(id)
    if activities:
        return jsonify({
            'success': False, 
            'message': 'Cannot delete category because it has associated activities'
        }), 400
    
    success = gitdb.delete_activity_category(id)
    if not success:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    return jsonify({'success': True})

# Activity Management
@app.route('/manage/activities')
def manage_activities():
    try:
        activities = gitdb.get_all_activities() or []
        categories = gitdb.get_all_activity_categories() or []
        
        # Log counts for debugging
        app.logger.info(f"Found {len(activities)} activities and {len(categories)} categories")
        
        return render_template('manage_activities.html', activities=activities, categories=categories)
    except Exception as e:
        app.logger.error(f"Error in manage_activities route: {str(e)}")
        # Return a simple error page if something goes wrong
        return render_template('error.html', 
                              error_title="Error Loading Activities", 
                              error_message="There was a problem loading activities and categories."), 500

@app.route('/api/activities', methods=['GET'])
def get_activities():
    activities = gitdb.get_all_activities()
    return jsonify({
        'success': True, 
        'activities': activities
    })

@app.route('/api/activities/by-category/<int:category_id>', methods=['GET'])
def get_activities_by_category(category_id):
    activities = gitdb.get_activities_by_category(category_id)
    return jsonify({
        'success': True, 
        'activities': activities
    })

@app.route('/api/activities', methods=['POST'])
def add_activity():
    data = request.json
    
    if not data.get('name'):
        return jsonify({'success': False, 'errors': {'name': ['Name is required']}}), 400
    
    if not data.get('category_id'):
        return jsonify({'success': False, 'errors': {'category_id': ['Category is required']}}), 400
    
    # Check if category exists
    category = gitdb.get_activity_category(data.get('category_id'))
    if not category:
        return jsonify({'success': False, 'errors': {'category_id': ['Category not found']}}), 400
    
    activity = gitdb.create_activity(data)
    
    return jsonify({'success': True, 'activity': activity})

@app.route('/api/activities/<int:id>', methods=['PUT'])
def update_activity(id):
    activity = gitdb.get_activity(id)
    if not activity:
        return jsonify({'success': False, 'message': 'Activity not found'}), 404
        
    data = request.json
    
    if not data.get('name'):
        return jsonify({'success': False, 'errors': {'name': ['Name is required']}}), 400
    
    if not data.get('category_id'):
        return jsonify({'success': False, 'errors': {'category_id': ['Category is required']}}), 400
    
    # Check if category exists
    category = gitdb.get_activity_category(data.get('category_id'))
    if not category:
        return jsonify({'success': False, 'errors': {'category_id': ['Category not found']}}), 400
    
    updated_activity = gitdb.update_activity(id, data)
    
    return jsonify({'success': True, 'activity': updated_activity})

@app.route('/api/activities/<int:id>', methods=['DELETE'])
def delete_activity(id):
    success = gitdb.delete_activity(id)
    if not success:
        return jsonify({'success': False, 'message': 'Activity not found'}), 404
    
    return jsonify({'success': True})

# Context processor to make sure current_user is available to templates
@app.context_processor
def inject_user():
    # Since we're not using Flask-Login anymore, we provide a dummy current_user
    current_user = {
        'is_authenticated': True,
        'is_admin': True,
        'id': 1,
        'username': 'admin'
    }
    return {'current_user': current_user}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 