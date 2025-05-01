import os
import json

@app.route('/activities')
def activities_list():
    """Display list of activities with their categories"""
    # Get all activities
    activities = []
    activities_dir = 'data/activities'
    if os.path.exists(activities_dir):
        for filename in os.listdir(activities_dir):
            if filename.endswith('.json'):
                with open(os.path.join(activities_dir, filename), 'r') as f:
                    try:
                        activity = json.load(f)
                        activities.append(activity)
                    except:
                        print(f"Error loading activity file: {filename}")
    
    # Get all categories and index them by ID
    categories = {}
    categories_dir = 'data/activity_categories'
    if os.path.exists(categories_dir):
        for filename in os.listdir(categories_dir):
            if filename.endswith('.json'):
                with open(os.path.join(categories_dir, filename), 'r') as f:
                    try:
                        category = json.load(f)
                        if 'id' in category:
                            categories[category['id']] = category
                    except:
                        print(f"Error loading category file: {filename}")
    
    # Debug output
    print(f"Loaded {len(activities)} activities and {len(categories)} categories")
    print(f"Categories: {categories}")
    
    # Add category_name to each activity for the template
    for activity in activities:
        category_id = activity.get('category_id')
        if category_id and category_id in categories:
            activity['category_name'] = categories[category_id].get('name', 'Unknown Category')
        else:
            activity['category_name'] = 'Unknown Category'
    
    return render_template('activities_list.html', 
                          activities=activities, 
                          categories=categories) 