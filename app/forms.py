from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, EmailField, TelField, FloatField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange

class CaregiverForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone Number', validators=[Optional()])
    max_hours_per_week = IntegerField('Max Hours per Week', validators=[Optional(), NumberRange(min=0, max=168)])
    max_hours_per_day = IntegerField('Max Hours per Day', validators=[Optional(), NumberRange(min=0, max=24)])
    max_days_per_week = IntegerField('Max Days per Week', validators=[Optional(), NumberRange(min=0, max=7)])
    rate = FloatField('Hourly Rate ($)', validators=[Optional(), NumberRange(min=0)])

class TemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional()]) 