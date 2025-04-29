import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a variable to store file paths for debugging
debug_info = []

# Try to list all Python files in the project
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            debug_info.append(f"Found Python file: {os.path.join(root, file)}")

# Try to import from app/main.py
try:
    from app.main import app
    debug_info.append("Successfully imported app from app.main")
except ImportError as e:
    debug_info.append(f"Error importing from app.main: {str(e)}")
    
    # Try importing directly from main.py
    try:
        sys.path.insert(0, './app')
        from main import app
        debug_info.append("Successfully imported app from main")
    except ImportError as e:
        debug_info.append(f"Error importing from main: {str(e)}")
        
        # As a last resort, try to print more diagnostic info
        print("\n".join(debug_info))
        raise

# This is what Gunicorn will import
application = app

def create_app():
    print("Debug info:", "\n".join(debug_info))
    return application

if __name__ == "__main__":
    application.run(debug=True, host='0.0.0.0') 