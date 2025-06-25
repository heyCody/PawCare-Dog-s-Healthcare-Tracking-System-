from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(),
        Length(min=10, max=10),
        Regexp('^[0-9]{10}$', message="Enter a valid 10-digit number")
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    dog_name = StringField("Dog's Name")
    dog_dob = DateField("Dog's Date of Birth", format='%Y-%m-%d')
    weight = FloatField("Weight (kg)")
    breed = SelectField("Breed", choices=[
        ('labrador', 'Labrador Retriever'),
        ('germanshepherd', 'German Shepherd'),
        ('goldenretriever', 'Golden Retriever'),
        ('poodle', 'Poodle'),
        ('bulldog', 'Bulldog'),
        ('beagle', 'Beagle'),
        ('rottweiler', 'Rottweiler'),
        ('doberman', 'Doberman'),
        ('dachshund', 'Dachshund'),
        ('shihtzu', 'Shih Tzu'),
        ('husky', 'Siberian Husky'),
        ('indian', 'Indian Pariah'),
        ('other', 'Other')
    ])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

