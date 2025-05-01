#!/usr/bin/env python3
"""
Fix script for activity categories directory inconsistency.
This script moves all JSON files from activity_categorys to activity_categories
and removes the incorrect directory.
"""

import os
import json
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_activity_categories')

# Define data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def fix_activity_categories():
    """Comprehensive fix for activity categories"""
    print("Starting comprehensive activity category fix...")
    
    # 1. Check if directories exist
    activities_dir = os.path.join(DATA_DIR, 'activities')
    categories_dir = os.path.join(DATA_DIR, 'activity_categories')
    
    # Check for incorrect plural forms
    old_activities_dir = os.path.join(DATA_DIR, 'activitys')
    old_categories_dir = os.path.join(DATA_DIR, 'activity_categorys')
    
    # Create directories if they don't exist
    for directory in [activities_dir, categories_dir]:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory)
    
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
        os.rmdir(old_activities_dir)
    
    if os.path.exists(old_categories_dir):
        print(f"Found incorrect categories directory: {old_categories_dir}")
        for filename in os.listdir(old_categories_dir):
            if filename.endswith('.json'):
                src = os.path.join(old_categories_dir, filename)
                dst = os.path.join(categories_dir, filename)
                print(f"Moving {src} to {dst}")
                shutil.move(src, dst)
        print(f"Removing directory: {old_categories_dir}")
        os.rmdir(old_categories_dir)
    
    # 2. Load all categories
    categories = {}
    if os.path.exists(categories_dir):
        for filename in os.listdir(categories_dir):
            if filename.endswith('.json'):
                with open(os.path.join(categories_dir, filename), 'r') as f:
                    try:
                        category = json.load(f)
                        if 'id' in category:
                            categories[category['id']] = category
                            print(f"Loaded category: {category.get('name', 'Unknown')} (ID: {category['id']})")
                        else:
                            print(f"Warning: Category in {filename} has no ID")
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON in category file {filename}")
    
    print(f"Loaded {len(categories)} categories")
    
    # 3. Check and fix activities
    if os.path.exists(activities_dir):
        for filename in os.listdir(activities_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(activities_dir, filename)
                with open(file_path, 'r') as f:
                    try:
                        activity = json.load(f)
                        activity_name = activity.get('name', 'Unknown')
                        
                        # Check if activity has category_id
                        if 'category_id' not in activity:
                            print(f"Activity '{activity_name}' has no category_id")
                            # You could set a default category here if you want
                            # activity['category_id'] = default_category_id
                        else:
                            category_id = activity['category_id']
                            if category_id not in categories and category_id is not None:
                                print(f"Activity '{activity_name}' references non-existent category ID: {category_id}")
                                # Option: Remove invalid reference
                                activity['category_id'] = None
                        
                        # Add category_name field directly to activity
                        if activity.get('category_id') and activity['category_id'] in categories:
                            activity['category_name'] = categories[activity['category_id']].get('name', 'Unknown Category')
                        else:
                            activity['category_name'] = 'Unknown Category'
                        
                        # Save updated activity
                        with open(file_path, 'w') as f:
                            json.dump(activity, f, indent=2)
                            print(f"Updated activity: {activity_name}")
                    
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON in activity file {filename}")

if __name__ == "__main__":
    logger.info("Starting activity categories directory fix")
    fix_activity_categories()
    logger.info("Fix completed") 