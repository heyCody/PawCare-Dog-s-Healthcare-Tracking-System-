# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

# models.py

# ... (rest of your imports) ...

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # --- CHANGE THIS LINE ---
    password = db.Column(db.String(255), nullable=False) # Increased length to 255
    # --- END CHANGE ---
    is_email_verified = db.Column(db.Boolean, default=False)
    mobile = db.Column(db.String(20))

    pets = db.relationship('Pet', backref='owner', lazy=True)

# ... (rest of your models: EmailOTP, Pet, VaccineRecord) ...

    # REMOVE any direct relationship like this from User:
    # vaccine_records = db.relationship('VaccineRecord', backref='user', lazy=True)
    # Vaccine records are related to pets, not directly to users.
    # You access a user's vaccine records via their pets: user.pets[0].vaccinations

class EmailOTP(db.Model):
    __tablename__ = 'email_otp'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def is_valid(self):
        return (datetime.utcnow() - self.created_at) < timedelta(minutes=5)

class Pet(db.Model):
    __tablename__ = 'pet' # Explicitly set table name to 'pet'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    breed = db.Column(db.String(100))
    dob = db.Column(db.Date)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key to user.id
    weight = db.Column(db.Float)

    # A pet has many vaccine records
    vaccinations = db.relationship('VaccineRecord', backref='pet_info', lazy=True)

class VaccineRecord(db.Model):
    __tablename__ = 'vaccination' # Explicitly set table name to 'vaccination'
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to pet.id (this is correct)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    vaccine_name = db.Column(db.String(100), nullable=False)
    vaccine_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date)