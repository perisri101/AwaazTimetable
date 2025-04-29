import sqlite3
import os

print("Starting database fix script...")
print("Current directory:", os.getcwd())

# Try multiple possible database locations
possible_paths = [
    'instance/scheduler.db',       # Flask's default instance path
    'scheduler.db',                # Root directory
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
    print("Database file not found!")
    print("Directory contents:", os.listdir("."))
    if os.path.exists('instance'):
        print("Instance directory contents:", os.listdir("instance"))
    exit(1)

try:
    # Connect directly to the database
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    
    # Check if caregiver table exists
    if ('caregiver',) not in tables:
        print("Caregiver table not found!")
        exit(1)
    
    # Check if rate column exists
    cursor.execute("PRAGMA table_info(caregiver)")
    columns = cursor.fetchall()
    print(f"Caregiver table columns: {columns}")
    column_names = [column[1] for column in columns]
    
    if 'rate' not in column_names:
        print("Adding rate column to caregiver table...")
        try:
            cursor.execute("ALTER TABLE caregiver ADD COLUMN rate FLOAT DEFAULT 0.0")
            conn.commit()
            print("Rate column added successfully!")
        except sqlite3.OperationalError as e:
            print(f"Error adding column: {str(e)}")
            
            # Try more aggressive approach - create temporary table and copy data
            print("Trying alternative approach with table recreation...")
            cursor.execute("BEGIN TRANSACTION")
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE caregiver_temp (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    max_hours_per_week INTEGER DEFAULT 40,
                    max_hours_per_day INTEGER DEFAULT 8,
                    max_days_per_week INTEGER DEFAULT 5,
                    rate FLOAT DEFAULT 0.0,
                    created_at DATETIME
                )
            """)
            
            # Copy data
            cursor.execute("""
                INSERT INTO caregiver_temp(id, name, email, phone, max_hours_per_week, 
                max_hours_per_day, max_days_per_week, created_at)
                SELECT id, name, email, phone, max_hours_per_week, 
                max_hours_per_day, max_days_per_week, created_at
                FROM caregiver
            """)
            
            # Drop original table
            cursor.execute("DROP TABLE caregiver")
            
            # Rename temp table
            cursor.execute("ALTER TABLE caregiver_temp RENAME TO caregiver")
            
            # Commit changes
            conn.commit()
            print("Table recreated successfully with rate column!")
    else:
        print("Rate column already exists.")
    
    # Check if activity_id column exists in checklist_item table
    cursor.execute("PRAGMA table_info(checklist_item)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'activity_id' not in column_names:
        print("Adding activity_id column to checklist_item table...")
        try:
            cursor.execute("ALTER TABLE checklist_item ADD COLUMN activity_id INTEGER")
            conn.commit()
            print("activity_id column added successfully!")
        except Exception as e:
            print(f"Error adding activity_id column: {str(e)}")
            conn.rollback()
    
    conn.close()
    print("Database fix completed successfully!")
except Exception as e:
    print(f"Error during database fix: {str(e)}")
    exit(1) 