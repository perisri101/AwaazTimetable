import os
import json

def fix_activity_category_references():
    """Check and fix activity category references"""
    # Get all categories
    categories = {}
    categories_dir = 'data/activity_categories'
    if os.path.exists(categories_dir):
        for filename in os.listdir(categories_dir):
            if filename.endswith('.json'):
                with open(os.path.join(categories_dir, filename), 'r') as f:
                    category = json.load(f)
                    categories[category.get('id')] = category
    
    # Check all activities
    activities_dir = 'data/activities'
    if os.path.exists(activities_dir):
        for filename in os.listdir(activities_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(activities_dir, filename)
                with open(file_path, 'r') as f:
                    activity = json.load(f)
                
                category_id = activity.get('category_id')
                if category_id and category_id not in categories:
                    print(f"Activity {activity.get('name')} references non-existent category {category_id}")
                    # Option 1: Remove invalid category reference
                    activity['category_id'] = None
                    # Option 2: Set to a default category if you have one
                    # activity['category_id'] = default_category_id
                    
                    # Save the updated activity
                    with open(file_path, 'w') as f:
                        json.dump(activity, f, indent=2)

if __name__ == "__main__":
    fix_activity_category_references() 