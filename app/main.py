from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
import os
import json
from models import db, User, Caregiver, Template, Calendar, Shift, ChecklistItem
from forms import LoginForm, UserForm, CaregiverForm, TemplateForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-awaaz-flexy-timetable')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and create admin user
def create_tables():
    with app.app_context():
        # Check if we need to add the rate column to existing database
        import sqlite3
        import os
        
        db_path = 'instance/scheduler.db'
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if rate column exists
                cursor.execute("PRAGMA table_info(caregiver)")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                
                if 'rate' not in column_names:
                    print("Adding rate column to caregiver table...")
                    cursor.execute("ALTER TABLE caregiver ADD COLUMN rate FLOAT DEFAULT 0.0")
                    conn.commit()
                    print("Rate column added successfully!")
                
                conn.close()
            except Exception as e:
                print(f"Error checking/adding rate column: {str(e)}")
                # If we can't modify the existing table, recreate the database
                try:
                    os.remove(db_path)
                    print("Removed corrupted database file. Will recreate.")
                except:
                    pass
        
        # Create tables
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

# Call the function to initialize the database
create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    templates = Template.query.all()
    calendars = Calendar.query.all()
    return render_template('dashboard.html', templates=templates, calendars=calendars)

# Management routes for admins
@app.route('/manage/caregivers')
@login_required
def manage_caregivers():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    caregivers = Caregiver.query.all()
    form = CaregiverForm()
    return render_template('manage_caregivers.html', caregivers=caregivers, form=form)

@app.route('/manage/caregivers/add', methods=['POST'])
@login_required
def add_caregiver():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
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
    if not errors.get('email') and Caregiver.query.filter_by(email=data.get('email')).first():
        errors['email'] = ['Email already in use']
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        rate_value = float(data.get('rate', 0)) if data.get('rate') else 0
    except ValueError:
        errors['rate'] = ['Rate must be a valid number']
        return jsonify({'success': False, 'errors': errors}), 400
    
    # Create new caregiver
    caregiver = Caregiver(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        rate=rate_value,
        max_hours_per_week=data.get('max_hours_per_week') or 40,
        max_hours_per_day=data.get('max_hours_per_day') or 8,
        max_days_per_week=data.get('max_days_per_week') or 5
    )
    db.session.add(caregiver)
    db.session.commit()
    return jsonify({'success': True, 'caregiver': caregiver.to_dict()})

@app.route('/manage/caregivers/edit/<int:id>', methods=['POST'])
@login_required
def edit_caregiver(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    caregiver = Caregiver.query.get_or_404(id)
    
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
    existing = Caregiver.query.filter_by(email=data.get('email')).first()
    if not errors.get('email') and existing and existing.id != id:
        errors['email'] = ['Email already in use']
    
    try:
        rate_value = float(data.get('rate', 0)) if data.get('rate') else 0
    except ValueError:
        errors['rate'] = ['Rate must be a valid number']
        return jsonify({'success': False, 'errors': errors}), 400
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    # Update caregiver
    caregiver.name = data.get('name')
    caregiver.email = data.get('email')
    caregiver.phone = data.get('phone')
    caregiver.rate = rate_value
    caregiver.max_hours_per_week = data.get('max_hours_per_week') or 40
    caregiver.max_hours_per_day = data.get('max_hours_per_day') or 8
    caregiver.max_days_per_week = data.get('max_days_per_week') or 5
    db.session.commit()
    return jsonify({'success': True, 'caregiver': caregiver.to_dict()})

@app.route('/manage/caregivers/delete/<int:id>', methods=['POST'])
@login_required
def delete_caregiver(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    caregiver = Caregiver.query.get_or_404(id)
    db.session.delete(caregiver)
    db.session.commit()
    return jsonify({'success': True})

# Template routes
@app.route('/templates')
@login_required
def list_templates():
    templates = Template.query.all()
    return render_template('templates/list.html', templates=templates)

@app.route('/templates/new', methods=['GET', 'POST'])
@login_required
def new_template():
    form = TemplateForm()
    if form.validate_on_submit():
        template = Template(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(template)
        db.session.commit()
        flash('Template created successfully')
        return redirect(url_for('edit_template', id=template.id))
    
    return render_template('templates/new.html', form=form)

@app.route('/templates/edit/<int:id>')
@login_required
def edit_template(id):
    template = Template.query.get_or_404(id)
    caregivers = Caregiver.query.all()
    return render_template('templates/edit.html', template=template, caregivers=caregivers)

@csrf.exempt
@app.route('/api/templates/<int:id>/shifts')
@login_required
def get_template_shifts(id):
    template = Template.query.get_or_404(id)
    return jsonify({
        'shifts': [shift.to_dict() for shift in template.shifts],
        'checklists': [item.to_dict() for item in template.checklist_items]
    })

@csrf.exempt
@app.route('/api/templates/<int:id>/shifts', methods=['POST'])
@login_required
def update_template_shifts(id):
    template = Template.query.get_or_404(id)
    data = request.json
    
    try:
        # Clear existing shifts
        for shift in template.shifts:
            db.session.delete(shift)
        
        # Add new shifts
        for shift_data in data.get('shifts', []):
            shift = Shift(
                template_id=template.id,
                day_of_week=shift_data['day_of_week'],
                start_hour=shift_data['start_hour'],
                end_hour=shift_data['end_hour'],
                caregiver_id=shift_data['caregiver_id']
            )
            db.session.add(shift)
        
        # Clear existing checklist items
        for item in template.checklist_items:
            db.session.delete(item)
        
        # Add new checklist items
        for item_data in data.get('checklists', []):
            item = ChecklistItem(
                template_id=template.id,
                day_of_week=item_data['day_of_week'],
                start_hour=item_data['start_hour'],
                end_hour=item_data['end_hour'],
                description=item_data['description']
            )
            db.session.add(item)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print("Error saving template:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
def delete_template(id):
    template = Template.query.get_or_404(id)
    
    # Check if template is being used by any calendars
    if Calendar.query.filter_by(template_id=id).first():
        flash('Cannot delete template because it is being used by one or more calendars.', 'danger')
        return redirect(url_for('list_templates'))
    
    # Delete template shifts and checklist items
    for shift in template.shifts:
        db.session.delete(shift)
    
    for item in template.checklist_items:
        db.session.delete(item)
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Template deleted successfully', 'success')
    return redirect(url_for('list_templates'))

# Calendar routes
@app.route('/calendars')
@login_required
def list_calendars():
    calendars = Calendar.query.all()
    return render_template('calendars/list.html', calendars=calendars)

@app.route('/calendars/new')
@login_required
def new_calendar():
    templates = Template.query.all()
    return render_template('calendars/new.html', templates=templates)

@app.route('/api/calendars/create', methods=['POST'])
@login_required
def create_calendar():
    data = request.json
    template = Template.query.get_or_404(data['template_id'])
    
    calendar = Calendar(
        name=data['name'],
        description=data.get('description', ''),
        template_id=template.id,
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        created_by=current_user.id
    )
    db.session.add(calendar)
    db.session.commit()
    
    # Copy template shifts and checklist items to calendar
    for template_shift in template.shifts:
        shift = Shift(
            calendar_id=calendar.id,
            day_of_week=template_shift.day_of_week,
            start_hour=template_shift.start_hour,
            end_hour=template_shift.end_hour,
            caregiver_id=template_shift.caregiver_id
        )
        db.session.add(shift)
    
    for template_item in template.checklist_items:
        item = ChecklistItem(
            calendar_id=calendar.id,
            day_of_week=template_item.day_of_week,
            start_hour=template_item.start_hour,
            end_hour=template_item.end_hour,
            description=template_item.description,
            completed=False
        )
        db.session.add(item)
    
    db.session.commit()
    return jsonify({'success': True, 'calendar_id': calendar.id})

@app.route('/calendars/view/<int:id>')
@login_required
def view_calendar(id):
    calendar = Calendar.query.get_or_404(id)
    caregivers = Caregiver.query.all()
    return render_template('calendars/view.html', calendar=calendar, caregivers=caregivers)

@app.route('/api/calendars/<int:id>/shifts')
@login_required
def get_calendar_shifts(id):
    calendar = Calendar.query.get_or_404(id)
    return jsonify({
        'shifts': [shift.to_dict() for shift in calendar.shifts],
        'checklists': [item.to_dict() for item in calendar.checklist_items]
    })

@app.route('/calendars/reports/<int:id>')
@login_required
def calendar_reports(id):
    calendar = Calendar.query.get_or_404(id)
    return render_template('calendars/reports.html', calendar=calendar)

@app.route('/api/calendars/<int:id>/reports')
@login_required
def get_calendar_reports(id):
    calendar = Calendar.query.get_or_404(id)
    
    # Calculate hours by caregiver
    caregiver_hours = {}
    total_cost = 0
    
    # First pass: collect all hours
    for shift in calendar.shifts:
        caregiver_id = shift.caregiver_id
        hours = shift.end_hour - shift.start_hour
        
        if caregiver_id not in caregiver_hours:
            caregiver = Caregiver.query.get(caregiver_id)
            caregiver_hours[caregiver_id] = {
                'name': caregiver.name,
                'total_hours': 0,
                'days': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'rate': caregiver.rate,
                'overtime_hours': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'regular_hours': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
                'cost': 0
            }
        
        caregiver_hours[caregiver_id]['total_hours'] += hours
        caregiver_hours[caregiver_id]['days'][shift.day_of_week] += hours
        
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
    
    for shift in calendar.shifts:
        day = shift.day_of_week
        for hour in range(shift.start_hour, shift.end_hour, 2):
            caregiver = Caregiver.query.get(shift.caregiver_id)
            hours_by_time[day][hour]['caregivers'].append(caregiver.name)
            hours_by_time[day][hour]['count'] += 1
    
    return jsonify({
        'caregiver_hours': caregiver_hours,
        'hours_by_time': hours_by_time,
        'total_cost': total_cost
    })

@app.route('/calendars/delete/<int:id>', methods=['POST'])
@login_required
def delete_calendar(id):
    calendar = Calendar.query.get_or_404(id)
    
    # Delete calendar shifts and checklist items
    for shift in calendar.shifts:
        db.session.delete(shift)
    
    for item in calendar.checklist_items:
        db.session.delete(item)
    
    db.session.delete(calendar)
    db.session.commit()
    
    flash('Calendar deleted successfully', 'success')
    return redirect(url_for('list_calendars'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 