import os
import json

def check_category_data():
    """Check the structure of category data files"""
    print("Checking category data structure...")
    
    categories_dir = 'data/activity_categories'
    if not os.path.exists(categories_dir):
        print(f"Error: Categories directory '{categories_dir}' does not exist!")
        return
    
    print(f"Found categories directory: {categories_dir}")
    files = os.listdir(categories_dir)
    print(f"Files in directory: {files}")
    
    for filename in files:
        if filename.endswith('.json'):
            file_path = os.path.join(categories_dir, filename)
            with open(file_path, 'r') as f:
                try:
                    category = json.load(f)
                    print(f"Category: {category.get('name', 'Unknown')}")
                    print(f"  ID: {category.get('id', 'Missing')}")
                    print("  Full data:", category)
                    print("---")
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON in file {filename}")

if __name__ == "__main__":
    check_category_data() 