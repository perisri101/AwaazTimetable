import os
import json
import sys

def load_entity(entity_type, entity_id):
    """Load an entity from the data directory"""
    file_path = f"data/{entity_type}/{entity_id}.json"
    print(f"Attempting to load: {file_path}")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    print(f"File not found: {file_path}")
    return None

def get_all_entities(entity_type):
    """Get all entities of a specific type"""
    entities = []
    directory = f"data/{entity_type}"
    print(f"Looking for entities in: {directory}")
    if os.path.exists(directory):
        files = os.listdir(directory)
        print(f"Files found: {files}")
        for filename in files:
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as f:
                    entity = json.load(f)
                    entities.append(entity)
                    print(f"Loaded entity: {entity}")
    else:
        print(f"Directory not found: {directory}")
    return entities

def debug_activities_and_categories():
    """Debug activities and their categories"""
    print("\n=== DEBUGGING ACTIVITIES AND CATEGORIES ===\n")
    
    # Get all activities
    print("\nLOADING ACTIVITIES:")
    activities = get_all_entities('activities')
    print(f"\nTotal activities loaded: {len(activities)}")
    
    # Get all categories
    print("\nLOADING CATEGORIES:")
    categories = get_all_entities('activity_categories')
    print(f"\nTotal categories loaded: {len(categories)}")
    
    # Create category lookup
    category_dict = {}
    for category in categories:
        if 'id' in category:
            category_dict[category['id']] = category
            print(f"Added category to lookup: {category['id']} -> {category.get('name', 'No name')}")
    
    print("\nCATEGORY LOOKUP DICTIONARY:")
    print(category_dict)
    
    # Check each activity's category
    print("\nCHECKING ACTIVITY CATEGORIES:")
    for activity in activities:
        print(f"\nActivity: {activity.get('name', 'Unknown')}")
        category_id = activity.get('category_id')
        print(f"  Category ID: {category_id}")
        
        if category_id:
            if category_id in category_dict:
                category_name = category_dict[category_id].get('name', 'Unknown')
                print(f"  Category found: {category_name}")
            else:
                print(f"  Category ID not found in lookup dictionary!")
        else:
            print("  No category ID assigned")

if __name__ == "__main__":
    debug_activities_and_categories() 