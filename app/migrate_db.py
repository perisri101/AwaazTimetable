from flask import Flask
from models import db, User, Caregiver, Template, Calendar, Shift, ChecklistItem
import sqlite3
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_rate_column():
    """Add the rate column to the caregiver table"""
    print("Starting migration to add rate column...")
    
    # Check multiple possible locations for the database file
    possible_paths = [
        'instance/scheduler.db',       # Flask's default instance path
        'scheduler.db',                # Root directory
        '../instance/scheduler.db',    # Parent's instance directory
        '/app/instance/scheduler.db',  # Docker volume mount
        '/app/scheduler.db'            # Docker root directory
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            print(f"Found database at: {path}")
            break
    
    if not db_path:
        print("Database file not found in any expected locations!")
        print("Current directory:", os.getcwd())
        print("Directory contents:", os.listdir("."))
        return
    
    try:
        # Connect directly to the database
        print(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if rate column exists
        cursor.execute("PRAGMA table_info(caregiver)")
        columns = cursor.fetchall()
        print(f"Existing columns: {columns}")
        column_names = [column[1] for column in columns]
        
        if 'rate' not in column_names:
            print("Adding rate column to caregiver table...")
            cursor.execute("ALTER TABLE caregiver ADD COLUMN rate FLOAT DEFAULT 0.0")
            conn.commit()
            print("Rate column added successfully!")
        else:
            print("Rate column already exists.")
            
        conn.close()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        # Try to fix by recreating database schema
        print("Attempting to recreate database schema...")
        try:
            with app.app_context():
                db.create_all()
                print("Database schema recreated successfully!")
        except Exception as e2:
            print(f"Failed to recreate schema: {str(e2)}")

if __name__ == "__main__":
    with app.app_context():
        add_rate_column() 