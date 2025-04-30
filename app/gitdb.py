import os
import json
import shutil
import logging
from datetime import datetime
from .git_utils import commit_and_push

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [GitDB] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('GitDB')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Ensure data directories exist
for dir_name in ['caregivers', 'templates', 'calendars', 'shifts', 'checklists', 
                 'activities', 'activity_categories']:
    os.makedirs(os.path.join(DATA_DIR, dir_name), exist_ok=True)

def _get_meta():
    """Get next ID from meta.json"""
    # Ensure DATA_DIR exists
    if not os.path.exists(DATA_DIR):
        logger.info(f"Creating data directory: {DATA_DIR}")
        os.makedirs(DATA_DIR)
    
    meta_path = os.path.join(DATA_DIR, 'meta.json')
    
    if not os.path.exists(meta_path):
        meta = {
            'next_ids': {
                'caregiver': 1,
                'template': 1,
                'calendar': 1,
                'shift': 1,
                'checklist_item': 1,
                'activity': 1,
                'activity_category': 1
            }
        }
        _save_meta(meta)
        return meta
    
    with open(meta_path, 'r') as f:
        return json.load(f)

def _save_meta(meta):
    """Save meta.json file"""
    # Ensure DATA_DIR exists
    if not os.path.exists(DATA_DIR):
        logger.info(f"Creating data directory: {DATA_DIR}")
        os.makedirs(DATA_DIR)
        
    meta_path = os.path.join(DATA_DIR, 'meta.json')
    
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    _safe_commit("Updated meta.json with new ID counters")

def _get_next_id(entity_type):
    """Get next ID for an entity type and increment the counter"""
    meta = _get_meta()
    next_id = meta['next_ids'][entity_type]
    meta['next_ids'][entity_type] = next_id + 1
    _save_meta(meta)
    return next_id

def _save_entity(entity_type, entity_data):
    """Save an entity to a JSON file"""
    try:
        id = entity_data['id']
        
        # Ensure the directory exists
        # Handle special case for activity_category => activity_categories
        # This is necessary because the normal pluralization (entity_type + 's')
        # would result in 'activity_categorys' which is grammatically incorrect.
        # Other functions like get_activity_category already use 'activity_categories'.
        if entity_type == 'activity_category':
            entity_dir = os.path.join(DATA_DIR, 'activity_categories')
        else:
            entity_dir = os.path.join(DATA_DIR, f"{entity_type}s")
            
        if not os.path.exists(entity_dir):
            logging.info(f"Creating directory for {entity_type}s: {entity_dir}")
            os.makedirs(entity_dir)
        
        file_path = os.path.join(entity_dir, f"{id}.json")
        
        logger.info(f"Saving {entity_type} with ID {id} to {file_path}")
        with open(file_path, 'w') as f:
            json.dump(entity_data, f, indent=2)
        
        # Commit changes if not in bulk operation
        if not os.environ.get('GITDB_BULK_OPERATION'):
            logger.info(f"Triggering Git commit for {entity_type} ID: {id}")
            try:
                # Check if current app has Git persistence enabled
                from flask import current_app
                git_enabled = current_app.config.get('GIT_PERSISTENCE_ENABLED', False)
                
                if git_enabled:
                    logger.info(f"Git persistence is enabled, committing changes")
                    from .git_utils import commit_and_push
                    commit_result = commit_and_push(f"Updated {entity_type} {id}")
                    logger.info(f"Git commit result: {'Success' if commit_result else 'Failed'}")
                else:
                    logger.warning("Git persistence is disabled, changes saved locally only")
                # If git is not enabled, we just saved the file locally which is fine
            except Exception as e:
                # If there's any error accessing the app context, just proceed silently
                # The file is already saved locally at this point
                logger.error(f"Error during Git commit: {str(e)}")
                print(f"Note: Git persistence skipped: {str(e)}")
                pass
        
        return True
    except Exception as e:
        logging.error(f"Error saving {entity_type} {id}: {str(e)}")
        raise

# --- Caregiver functions ---

def get_caregiver(id):
    """Get a caregiver by ID"""
    file_path = os.path.join(DATA_DIR, 'caregivers', f"{id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_all_caregivers():
    """Get all caregivers"""
    caregivers_dir = os.path.join(DATA_DIR, 'caregivers')
    caregivers = []
    
    if not os.path.exists(caregivers_dir):
        return caregivers
    
    for filename in os.listdir(caregivers_dir):
        if filename.endswith('.json'):
            with open(os.path.join(caregivers_dir, filename), 'r') as f:
                caregivers.append(json.load(f))
    
    return caregivers

def create_caregiver(data):
    """Create a new caregiver"""
    id = _get_next_id('caregiver')
    
    caregiver = {
        'id': id,
        'name': data.get('name'),
        'email': data.get('email'),
        'phone': data.get('phone', ''),
        'max_hours_per_week': data.get('max_hours_per_week', 40),
        'max_hours_per_day': data.get('max_hours_per_day', 8),
        'max_days_per_week': data.get('max_days_per_week', 5),
        'rate': data.get('rate', 0.0),
        'created_at': datetime.utcnow().isoformat()
    }
    
    _save_entity('caregiver', caregiver)
    return caregiver

def update_caregiver(id, data):
    """Update a caregiver"""
    caregiver = get_caregiver(id)
    
    if not caregiver:
        return None
    
    # Update fields
    for key in ['name', 'email', 'phone', 'max_hours_per_week', 
                'max_hours_per_day', 'max_days_per_week', 'rate']:
        if key in data:
            caregiver[key] = data[key]
    
    _save_entity('caregiver', caregiver)
    return caregiver

def delete_caregiver(id):
    """Delete a caregiver"""
    file_path = os.path.join(DATA_DIR, 'caregivers', f"{id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    os.remove(file_path)
    
    try:
        from flask import current_app
        git_enabled = current_app.config.get('GIT_PERSISTENCE_ENABLED', False)
        if git_enabled:
            commit_and_push(f"Deleted caregiver {id}")
    except Exception:
        pass
    
    return True

# --- Template functions ---

def get_template(id):
    """Get a template by ID"""
    file_path = os.path.join(DATA_DIR, 'templates', f"{id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_all_templates():
    """Get all templates"""
    templates_dir = os.path.join(DATA_DIR, 'templates')
    templates = []
    
    if not os.path.exists(templates_dir):
        return templates
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.json'):
            with open(os.path.join(templates_dir, filename), 'r') as f:
                templates.append(json.load(f))
    
    return templates

def create_template(data):
    """Create a new template"""
    id = _get_next_id('template')
    
    template = {
        'id': id,
        'name': data.get('name'),
        'description': data.get('description', ''),
        'created_by': data.get('created_by', 1),  # Default to admin user
        'created_at': datetime.utcnow().isoformat()
    }
    
    _save_entity('template', template)
    return template

def update_template(id, data):
    """Update a template"""
    template = get_template(id)
    
    if not template:
        return None
    
    for key in ['name', 'description']:
        if key in data:
            template[key] = data[key]
    
    _save_entity('template', template)
    return template

def delete_template(id):
    """Delete a template and its related shifts/checklists"""
    file_path = os.path.join(DATA_DIR, 'templates', f"{id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    # Get shifts and checklists for this template
    shifts_file = os.path.join(DATA_DIR, 'shifts', f"template-{id}-shifts.json")
    checklists_file = os.path.join(DATA_DIR, 'checklists', f"template-{id}-checklists.json")
    
    # Delete related files
    for f in [shifts_file, checklists_file, file_path]:
        if os.path.exists(f):
            os.remove(f)
    
    _safe_commit(f"Deleted template {id} and related data")
    return True

# --- Shift functions ---

def get_template_shifts(template_id):
    """Get all shifts for a template"""
    file_path = os.path.join(DATA_DIR, 'shifts', f"template-{template_id}-shifts.json")
    
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_template_shifts(template_id, shifts):
    """Save shifts for a template"""
    # Ensure the shifts directory exists
    shifts_dir = os.path.join(DATA_DIR, 'shifts')
    if not os.path.exists(shifts_dir):
        os.makedirs(shifts_dir)
        
    file_path = os.path.join(shifts_dir, f"template-{template_id}-shifts.json")
    with open(file_path, 'w') as f:
        json.dump(shifts, f, indent=2)
    
    _safe_commit(f"Updated shifts for template {template_id}")

def get_calendar_shifts(calendar_id):
    """Get all shifts for a calendar"""
    file_path = os.path.join(DATA_DIR, 'shifts', f"calendar-{calendar_id}-shifts.json")
    
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_calendar_shifts(calendar_id, shifts):
    """Save shifts for a calendar"""
    # Ensure the shifts directory exists
    shifts_dir = os.path.join(DATA_DIR, 'shifts')
    if not os.path.exists(shifts_dir):
        os.makedirs(shifts_dir)
        
    file_path = os.path.join(shifts_dir, f"calendar-{calendar_id}-shifts.json")
    with open(file_path, 'w') as f:
        json.dump(shifts, f, indent=2)
    
    _safe_commit(f"Updated shifts for calendar {calendar_id}")

# --- Checklist functions ---

def get_template_checklists(template_id):
    """Get all checklist items for a template"""
    file_path = os.path.join(DATA_DIR, 'checklists', f"template-{template_id}-checklists.json")
    
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_template_checklists(template_id, checklists):
    """Save checklist items for a template"""
    # Ensure the checklists directory exists
    checklists_dir = os.path.join(DATA_DIR, 'checklists')
    if not os.path.exists(checklists_dir):
        os.makedirs(checklists_dir)
        
    file_path = os.path.join(DATA_DIR, 'checklists', f"template-{template_id}-checklists.json")
    with open(file_path, 'w') as f:
        json.dump(checklists, f, indent=2)
    
    _safe_commit(f"Updated checklists for template {template_id}")

def get_calendar_checklists(calendar_id):
    """Get all checklist items for a calendar"""
    file_path = os.path.join(DATA_DIR, 'checklists', f"calendar-{calendar_id}-checklists.json")
    
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_calendar_checklists(calendar_id, checklists):
    """Save checklist items for a calendar"""
    # Ensure the checklists directory exists
    checklists_dir = os.path.join(DATA_DIR, 'checklists')
    if not os.path.exists(checklists_dir):
        os.makedirs(checklists_dir)
        
    file_path = os.path.join(DATA_DIR, 'checklists', f"calendar-{calendar_id}-checklists.json")
    with open(file_path, 'w') as f:
        json.dump(checklists, f, indent=2)
    
    _safe_commit(f"Updated checklists for calendar {calendar_id}")

def get_checklist_item(id):
    """Get a checklist item by ID - search in all calendar and template checklists"""
    # Search in all calendar checklists
    calendars_dir = os.path.join(DATA_DIR, 'calendars')
    if os.path.exists(calendars_dir):
        for filename in os.listdir(calendars_dir):
            if filename.endswith('.json'):
                calendar_id = filename.split('.')[0]
                checklist_file = os.path.join(DATA_DIR, 'checklists', f"calendar-{calendar_id}-checklists.json")
                if os.path.exists(checklist_file):
                    with open(checklist_file, 'r') as f:
                        checklists = json.load(f)
                        for item in checklists:
                            if item['id'] == id:
                                return item, f"calendar-{calendar_id}"
    
    # Search in all template checklists
    templates_dir = os.path.join(DATA_DIR, 'templates')
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                template_id = filename.split('.')[0]
                checklist_file = os.path.join(DATA_DIR, 'checklists', f"template-{template_id}-checklists.json")
                if os.path.exists(checklist_file):
                    with open(checklist_file, 'r') as f:
                        checklists = json.load(f)
                        for item in checklists:
                            if item['id'] == id:
                                return item, f"template-{template_id}"
    
    return None, None

def toggle_checklist_item(id):
    """Toggle completion of checklist item"""
    item, file_prefix = get_checklist_item(id)
    
    if not item or not file_prefix:
        return None
    
    # Toggle completion
    item['completed'] = not item['completed']
    
    # Save back to the file
    checklist_file = os.path.join(DATA_DIR, 'checklists', f"{file_prefix}-checklists.json")
    with open(checklist_file, 'r') as f:
        checklists = json.load(f)
    
    # Find and update the item
    for i, list_item in enumerate(checklists):
        if list_item['id'] == id:
            checklists[i] = item
            break
    
    with open(checklist_file, 'w') as f:
        json.dump(checklists, f, indent=2)
    
    _safe_commit(f"Toggled checklist item {id}")
    return item

# --- Calendar functions ---

def get_calendar(id):
    """Get a calendar by ID"""
    file_path = os.path.join(DATA_DIR, 'calendars', f"{id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_all_calendars():
    """Get all calendars"""
    calendars_dir = os.path.join(DATA_DIR, 'calendars')
    calendars = []
    
    if not os.path.exists(calendars_dir):
        return calendars
    
    for filename in os.listdir(calendars_dir):
        if filename.endswith('.json'):
            with open(os.path.join(calendars_dir, filename), 'r') as f:
                calendars.append(json.load(f))
    
    return calendars

def create_calendar(data):
    """Create a new calendar from a template"""
    try:
        id = _get_next_id('calendar')
        template_id = data.get('template_id')
        
        # Ensure template_id is correct format
        if isinstance(template_id, str):
            template_id = int(template_id)
        
        # Create calendar entity
        calendar = {
            'id': id,
            'name': data.get('name'),
            'description': data.get('description', ''),
            'template_id': template_id,
            'start_date': data.get('start_date'),
            'created_by': data.get('created_by', 1),  # Default to admin user
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Ensure the calendar directory exists
        calendars_dir = os.path.join(DATA_DIR, 'calendars')
        if not os.path.exists(calendars_dir):
            os.makedirs(calendars_dir)
            
        # Ensure the shifts directory exists
        shifts_dir = os.path.join(DATA_DIR, 'shifts')
        if not os.path.exists(shifts_dir):
            os.makedirs(shifts_dir)
            
        # Ensure the checklists directory exists
        checklists_dir = os.path.join(DATA_DIR, 'checklists')
        if not os.path.exists(checklists_dir):
            os.makedirs(checklists_dir)
        
        _save_entity('calendar', calendar)
        
        # Copy shifts from template
        template_shifts = get_template_shifts(template_id)
        calendar_shifts = []
        
        if template_shifts:
            for shift in template_shifts:
                calendar_shift = shift.copy()
                calendar_shift['calendar_id'] = id
                calendar_shift['template_id'] = None
                calendar_shifts.append(calendar_shift)
        
        save_calendar_shifts(id, calendar_shifts)
        
        # Copy checklists from template
        template_checklists = get_template_checklists(template_id)
        calendar_checklists = []
        
        if template_checklists:
            for item in template_checklists:
                calendar_item = item.copy()
                calendar_item['calendar_id'] = id
                calendar_item['template_id'] = None
                calendar_item['id'] = _get_next_id('checklist_item')
                calendar_item['completed'] = False
                calendar_checklists.append(calendar_item)
        
        save_calendar_checklists(id, calendar_checklists)
        
        # Commit changes
        _safe_commit(f"Created new calendar: {calendar['name']} (ID: {id})")
        
        logging.info(f"Calendar created successfully: ID={id}, Name={calendar['name']}")
        return calendar
    except Exception as e:
        logging.error(f"Error creating calendar: {str(e)}")
        raise

def delete_calendar(id):
    """Delete a calendar and its related shifts/checklists"""
    file_path = os.path.join(DATA_DIR, 'calendars', f"{id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    # Get shifts and checklists for this calendar
    shifts_file = os.path.join(DATA_DIR, 'shifts', f"calendar-{id}-shifts.json")
    checklists_file = os.path.join(DATA_DIR, 'checklists', f"calendar-{id}-checklists.json")
    
    # Delete related files
    for f in [shifts_file, checklists_file, file_path]:
        if os.path.exists(f):
            os.remove(f)
    
    _safe_commit(f"Deleted calendar {id} and related data")
    return True

# --- Activity Category functions ---

def get_activity_category(id):
    """Get an activity category by ID"""
    file_path = os.path.join(DATA_DIR, 'activity_categories', f"{id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_all_activity_categories():
    """Get all activity categories"""
    categories_dir = os.path.join(DATA_DIR, 'activity_categories')
    categories = []
    
    if not os.path.exists(categories_dir):
        return categories
    
    for filename in os.listdir(categories_dir):
        if filename.endswith('.json'):
            with open(os.path.join(categories_dir, filename), 'r') as f:
                categories.append(json.load(f))
    
    return categories

def create_activity_category(data):
    """Create a new activity category"""
    id = _get_next_id('activity_category')
    
    category = {
        'id': id,
        'name': data.get('name'),
        'description': data.get('description', ''),
        'created_by': data.get('created_by', 1),  # Default to admin user
        'created_at': datetime.utcnow().isoformat()
    }
    
    _save_entity('activity_category', category)
    return category

def update_activity_category(id, data):
    """Update an activity category"""
    category = get_activity_category(id)
    
    if not category:
        return None
    
    for key in ['name', 'description']:
        if key in data:
            category[key] = data[key]
    
    _save_entity('activity_category', category)
    return category

def delete_activity_category(id):
    """Delete an activity category"""
    file_path = os.path.join(DATA_DIR, 'activity_categories', f"{id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    # Check if category has activities
    activities = get_all_activities()
    for activity in activities:
        if activity['category_id'] == id:
            return False
    
    os.remove(file_path)
    _safe_commit(f"Deleted activity category {id}")
    return True

# --- Activity functions ---

def get_activity(id):
    """Get an activity by ID"""
    file_path = os.path.join(DATA_DIR, 'activities', f"{id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_all_activities():
    """Get all activities"""
    activities_dir = os.path.join(DATA_DIR, 'activities')
    activities = []
    
    if not os.path.exists(activities_dir):
        return activities
    
    for filename in os.listdir(activities_dir):
        if filename.endswith('.json'):
            with open(os.path.join(activities_dir, filename), 'r') as f:
                activities.append(json.load(f))
    
    return activities

def get_activities_by_category(category_id):
    """Get all activities for a category"""
    activities = get_all_activities()
    return [a for a in activities if a['category_id'] == category_id]

def create_activity(data):
    """Create a new activity"""
    id = _get_next_id('activity')
    
    activity = {
        'id': id,
        'name': data.get('name'),
        'description': data.get('description', ''),
        'category_id': data.get('category_id'),
        'created_by': data.get('created_by', 1),  # Default to admin user
        'created_at': datetime.utcnow().isoformat()
    }
    
    _save_entity('activity', activity)
    return activity

def update_activity(id, data):
    """Update an activity"""
    activity = get_activity(id)
    
    if not activity:
        return None
    
    for key in ['name', 'description', 'category_id']:
        if key in data:
            activity[key] = data[key]
    
    _save_entity('activity', activity)
    return activity

def delete_activity(id):
    """Delete an activity"""
    file_path = os.path.join(DATA_DIR, 'activities', f"{id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    # Check if activity is used in checklist items
    # We'd need to implement a search through all checklist items
    # For simplicity, we'll just delete the activity for now
    
    os.remove(file_path)
    _safe_commit(f"Deleted activity {id}")
    return True

# Function to safely commit changes through Git if enabled
def _safe_commit(message):
    """Commit changes using Git if enabled"""
    logger.info(f"Safe commit requested: {message}")
    try:
        from flask import current_app
        git_enabled = current_app.config.get('GIT_PERSISTENCE_ENABLED', False)
        
        if git_enabled:
            logger.info("Git persistence is enabled, proceeding with commit")
            from .git_utils import commit_and_push
            commit_result = commit_and_push(message)
            logger.info(f"Git commit result: {'Success' if commit_result else 'Failed'}")
            return commit_result
        else:
            logger.warning("Git persistence is disabled, skipping commit")
            return True  # Return success since we're not actually expecting to commit
    except Exception as e:
        logger.error(f"Error in safe commit: {str(e)}")
        print(f"Git commit skipped: {str(e)}")
        return False

# Initialize meta.json if it doesn't exist
_get_meta() 