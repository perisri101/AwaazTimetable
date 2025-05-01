import os
import json
import shutil

def ensure_directory(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        os.makedirs(directory)

def load_json_file(file_path):
    """Load a JSON file with error handling"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}")
        return None
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None

def save_json_file(file_path, data):
    """Save data to a JSON file with error handling"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")
        return False

def fix_categories_comprehensive():
    """Comprehensive fix for activity categories"""
    print("Starting comprehensive category fix...")
    
    # Define directories
    data_dir = 'data'
    activities_dir = os.path.join(data_dir, 'activities')
    categories_dir = os.path.join(data_dir, 'activity_categories')
    
    # Check for incorrect plural forms
    old_activities_dir = os.path.join(data_dir, 'activitys')
    old_categories_dir = os.path.join(data_dir, 'activity_categorys')
    
    # Ensure directories exist
    ensure_directory(data_dir)
    ensure_directory(activities_dir)
    ensure_directory(categories_dir)
    
    # Move files from incorrect directories if they exist
    if os.path.exists(old_activities_dir):
        print(f"Found incorrect activities directory: {old_activities_dir}")
        for filename in os.listdir(old_activities_dir):
            if filename.endswith('.json'):
                src = os.path.join(old_activities_dir, filename)
                dst = os.path.join(activities_dir, filename)
                print(f"Moving {src} to {dst}")
                shutil.move(src, dst)
        print(f"Removing directory: {old_activities_dir}")
        try:
            os.rmdir(old_activities_dir)
        except:
            print(f"Could not remove directory: {old_activities_dir}")
    
    if os.path.exists(old_categories_dir):
        print(f"Found incorrect categories directory: {old_categories_dir}")
        for filename in os.listdir(old_categories_dir):
            if filename.endswith('.json'):
                src = os.path.join(old_categories_dir, filename)
                dst = os.path.join(categories_dir, filename)
                print(f"Moving {src} to {dst}")
                shutil.move(src, dst)
        print(f"Removing directory: {old_categories_dir}")
        try:
            os.rmdir(old_categories_dir)
        except:
            print(f"Could not remove directory: {old_categories_dir}")
    
    # Create a default category if none exist
    categories = []
    if os.path.exists(categories_dir):
        for filename in os.listdir(categories_dir):
            if filename.endswith('.json'):
                category = load_json_file(os.path.join(categories_dir, filename))
                if category:
                    categories.append(category)
    
    if not categories:
        print("No categories found. Creating a default category.")
        default_category = {
            "id": "default",
            "name": "Default Category",
            "description": "Default category created by fix script"
        }
        save_json_file(os.path.join(categories_dir, "default.json"), default_category)
        categories.append(default_category)
    
    # Create a lookup dictionary for categories
    category_dict = {}
    for category in categories:
        if 'id' in category:
            category_dict[category['id']] = category
            print(f"Category: {category.get('name', 'Unknown')} (ID: {category['id']})")
    
    # Fix activities
    if os.path.exists(activities_dir):
        for filename in os.listdir(activities_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(activities_dir, filename)
                activity = load_json_file(file_path)
                if not activity:
                    continue
                
                activity_name = activity.get('name', 'Unknown')
                print(f"Processing activity: {activity_name}")
                
                # Ensure activity has an ID
                if 'id' not in activity:
                    activity['id'] = os.path.splitext(filename)[0]
                    print(f"  Added missing ID: {activity['id']}")
                
                # Check category_id
                if 'category_id' not in activity or not activity['category_id'] or activity['category_id'] not in category_dict:
                    # Assign to default or first category
                    if 'default' in category_dict:
                        activity['category_id'] = 'default'
                    else:
                        activity['category_id'] = categories[0]['id']
                    print(f"  Updated category_id to: {activity['category_id']}")
                
                # Add category_name directly to activity for redundancy
                if activity['category_id'] in category_dict:
                    activity['category_name'] = category_dict[activity['category_id']].get('name', 'Unknown Category')
                    print(f"  Set category_name to: {activity['category_name']}")
                
                # Save updated activity
                save_json_file(file_path, activity)
    
    print("Comprehensive category fix completed.")

if __name__ == "__main__":
    fix_categories_comprehensive() 