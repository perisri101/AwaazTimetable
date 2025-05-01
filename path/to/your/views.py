def get_activity_category_name(category_id):
    """Retrieve the category name from the category ID"""
    try:
        # Assuming you're using the Git-based persistence mentioned in your README
        category = load_entity('activity_categories', category_id)
        return category.get('name', 'Unknown Category')
    except Exception as e:
        print(f"Error retrieving category: {e}")
        return 'Unknown Category'

# When preparing data for your template, make sure to include the category name
def activities_list():
    activities = get_all_activities()  # Your existing function to get activities
    
    # Add category name to each activity
    for activity in activities:
        category_id = activity.get('category_id')
        if category_id:
            activity['category_name'] = get_activity_category_name(category_id)
        else:
            activity['category_name'] = 'Unknown Category'
    
    return render_template('activities.html', activities=activities) 