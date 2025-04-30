from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    templates = db.relationship('Template', backref='creator', lazy=True)
    calendars = db.relationship('Calendar', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat()
        }

class Caregiver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    max_hours_per_week = db.Column(db.Integer, default=40)
    max_hours_per_day = db.Column(db.Integer, default=8)
    max_days_per_week = db.Column(db.Integer, default=5)
    rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shifts = db.relationship('Shift', backref='caregiver', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'max_hours_per_week': self.max_hours_per_week,
            'max_hours_per_day': self.max_hours_per_day,
            'max_days_per_week': self.max_days_per_week,
            'rate': self.rate
        }

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shifts = db.relationship('Shift', backref='template', lazy=True, 
                            primaryjoin="and_(Template.id==Shift.template_id, Shift.calendar_id==None)")
    checklist_items = db.relationship('ChecklistItem', backref='template', lazy=True,
                                    primaryjoin="and_(Template.id==ChecklistItem.template_id, ChecklistItem.calendar_id==None)")
    calendars = db.relationship('Calendar', backref='template', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shifts = db.relationship('Shift', backref='calendar', lazy=True,
                            primaryjoin="Calendar.id==Shift.calendar_id")
    checklist_items = db.relationship('ChecklistItem', backref='calendar', lazy=True,
                                    primaryjoin="Calendar.id==ChecklistItem.calendar_id")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_id': self.template_id,
            'start_date': self.start_date.isoformat(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id'))
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_hour = db.Column(db.Integer, nullable=False)   # 0-22 (even hours only for 2hr blocks)
    end_hour = db.Column(db.Integer, nullable=False)     # 2-24 (even hours only for 2hr blocks)
    caregiver_id = db.Column(db.Integer, db.ForeignKey('caregiver.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'calendar_id': self.calendar_id,
            'day_of_week': self.day_of_week,
            'start_hour': self.start_hour,
            'end_hour': self.end_hour,
            'caregiver_id': self.caregiver_id
        }

class ActivityCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    activities = db.relationship('Activity', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('activity_category.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id'))
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_hour = db.Column(db.Integer, nullable=False)   # 0-22 (even hours only for 2hr blocks)
    end_hour = db.Column(db.Integer, nullable=False)     # 2-24 (even hours only for 2hr blocks)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)  # Link to master activity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    activity = db.relationship('Activity', backref='checklist_items', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'calendar_id': self.calendar_id,
            'day_of_week': self.day_of_week,
            'start_hour': self.start_hour,
            'end_hour': self.end_hour,
            'description': self.description,
            'completed': self.completed,
            'activity_id': self.activity_id
        } 