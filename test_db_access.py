import os
import json
import sys

# Add your application's directory to the path if needed
# sys.path.append('/path/to/your/app')

# Import your database functions
# from app.gitdb import load_entity, get_all_entities

# If you can't import directly, define simplified versions here
def load_entity(entity_type, entity_id):
    """Load an entity from the data directory"""
    file_path = f"data/{entity_type}/{entity_id}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def get_all_entities(entity_type):
    """Get all entities of a specific type"""
    entities = []
    directory = f"data/{entity_type}"
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as f:
                    entities.append(json.load(f))
    return entities

def test_db_access():
    """Test database access functions"""
    print("Testing database access...")
    
    # Test loading categories
    print("\nTesting category loading:")
    categories = get_all_entities('activity_categories')
    print(f"Loaded {len(categories)} categories")
    for category in categories:
        print(f"  Category: {category.get('name', 'Unknown')} (ID: {category.get('id', 'Missing')})")
    
    # Test loading activities
    print("\nTesting activity loading:")
    activities = get_all_entities('activities')
    print(f"Loaded {len(activities)} activities")
    for activity in activities:
        print(f"  Activity: {activity.get('name', 'Unknown')}")
        category_id = activity.get('category_id')
        if category_id:
            category = load_entity('activity_categories', category_id)
            category_name = category.get('name', 'Unknown Category') if category else 'Unknown Category'
            print(f"    Category: {category_name} (ID: {category_id})")
        else:
            print(f"    No category assigned")

if __name__ == "__main__":
    test_db_access() 