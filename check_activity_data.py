import os
import json

def check_activity_data():
    """Check the structure of activity data files"""
    print("Checking activity data structure...")
    
    activities_dir = 'data/activities'
    if not os.path.exists(activities_dir):
        print(f"Error: Activities directory '{activities_dir}' does not exist!")
        return
    
    for filename in os.listdir(activities_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(activities_dir, filename)
            with open(file_path, 'r') as f:
                try:
                    activity = json.load(f)
                    print(f"Activity: {activity.get('name', 'Unknown')}")
                    print(f"  ID: {activity.get('id', 'Missing')}")
                    print(f"  Category ID: {activity.get('category_id', 'Missing')}")
                    print("  Full data:", activity)
                    print("---")
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON in file {filename}")

if __name__ == "__main__":
    check_activity_data() 