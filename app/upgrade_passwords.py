"""
One-time script to update password hashing from scrypt to pbkdf2:sha256 for compatibility
Run this when migrating from newer Python to older Python environments
"""

from flask import Flask
try:
    # Try local import first (when running directly in app directory)
    from models import db, User
except ImportError:
    # Try relative import (when running from project root)
    from .models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys

# Add parent directory to path for imports when running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Configure database
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Heroku Postgres uses 'postgres://' but SQLAlchemy expects 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///scheduler.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Default admin password to reset to if necessary
DEFAULT_ADMIN_PASSWORD = 'admin'

def update_password_hashes():
    """Update all user password hashes to use pbkdf2:sha256 instead of scrypt"""
    with app.app_context():
        try:
            # Get all users
            users = User.query.all()
            print(f"Found {len(users)} user(s) to update")
            
            admin_updated = False
            
            for user in users:
                try:
                    # For admin user, reset to default password
                    if user.username == 'admin':
                        user.set_password(DEFAULT_ADMIN_PASSWORD)
                        db.session.commit()
                        print(f"Reset admin user password to default")
                        admin_updated = True
                    # For regular users, we can't know their passwords, so we'd
                    # need to reset them or implement a proper migration strategy
                    else:
                        # Here we're just setting a random temporary password
                        # In a real app, you might want to email users a password reset link
                        temp_password = os.urandom(8).hex()
                        user.set_password(temp_password)
                        print(f"Reset user {user.username} password to temporary value")
                except Exception as e:
                    print(f"Error updating user {user.username}: {str(e)}")
                    continue
            
            # If no admin user was found/updated, create one
            if not admin_updated:
                try:
                    admin = User(username='admin', email='admin@example.com', is_admin=True)
                    admin.set_password(DEFAULT_ADMIN_PASSWORD)
                    db.session.add(admin)
                    db.session.commit()
                    print("Created new admin user with default password")
                except Exception as e:
                    print(f"Error creating admin user: {str(e)}")
            
            db.session.commit()
            print("Password hash update complete")
        except Exception as e:
            print(f"Error during password update: {str(e)}")
            # If an error occurs, ensure the admin user exists
            try:
                # Try to create admin user as a fallback
                admin = User(username='admin', email='admin@example.com', is_admin=True)
                admin.set_password(DEFAULT_ADMIN_PASSWORD)
                db.session.add(admin)
                db.session.commit()
                print("Created admin user as fallback")
            except:
                print("Failed to create admin user")

if __name__ == "__main__":
    update_password_hashes()
    print("Done!") 