# When saving an activity, ensure it has a valid category_id
def save_activity(activity_data):
    # Validate that the category exists
    category_id = activity_data.get('category_id')
    if category_id:
        category = load_entity('activity_categories', category_id)
        if not category:
            # Handle invalid category
            activity_data['category_id'] = None
    
    # Save the activity
    save_entity('activities', activity_data) 