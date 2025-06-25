# app.py (Full code with login route restored)

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from sqlalchemy import text
import os
import logging
from vaccine import vaccine_bp
from chatbot_module import chatbot_bp
from email_utils import SendEmail, generate_otp, build_otp_email
from models import db, User, Pet, VaccineRecord, EmailOTP

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=os.getenv('SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS") == 'True',
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAP_KEY=os.getenv("MAP_KEY")
)
@app.context_processor
def inject_google_api_key():
    return dict(MAP_KEY=os.getenv("MAP_KEY"))

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

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

# Initialize extensions
db.init_app(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register Blueprints
app.register_blueprint(chatbot_bp)
app.register_blueprint(vaccine_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html', Maps_key=app.config['MAP_KEY'], user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session.pop('temp_user', None)
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        mobile = form.mobile.data
        breed = form.breed.data
        dog_name = form.dog_name.data
        dog_dob = form.dog_dob.data
        weight = form.weight.data

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", 'danger')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        session['temp_user'] = {
            'name': name,
            'email': email,
            'mobile': mobile,
            'password': hashed_password,
            'dog_name': dog_name,
            'dog_dob': dog_dob.strftime('%Y-%m-%d') if dog_dob else None,
            'weight': weight,
            'breed': breed
        }

        otp = generate_otp()
        email_html = build_otp_email(otp)
        if SendEmail(email_html, email, "Your PawCare OTP Code").email_main_send():
            try:
                db.session.execute(db.delete(EmailOTP).where(EmailOTP.email == email))
                db.session.commit()
                db.session.add(EmailOTP(email=email, otp_code=str(otp)))
                db.session.commit()
                logging.debug(f"OTP saved for {email}: {otp}")
                return redirect(url_for('verify_otp'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Database error: {str(e)}")
                flash("Database error. Please try again.", 'danger')
        else:
            flash("Failed to send OTP email. Please try again.", 'danger')

    return render_template('signup.html', form=form)

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_entered = request.form.get('otp')
        temp_user = session.get('temp_user')

        if not temp_user:
            flash("Session expired. Please sign up again.", 'danger')
            return redirect(url_for('signup'))

        try:
            record = db.session.execute(
                db.select(EmailOTP)
                .filter_by(email=temp_user['email'], otp_code=otp_entered)
                .order_by(EmailOTP.created_at.desc())
            ).scalar_one_or_none()

            if record and record.is_valid():
                try:
                    # --- Start of User and Pet Creation ---
                    # 1. Create and Add the User
                    new_user = User(
                        name=temp_user['name'],
                        email=temp_user['email'],
                        password=temp_user['password'], # Password should already be hashed from signup
                        mobile=temp_user['mobile'], # <-- UNCOMMENTED THIS LINE
                        is_email_verified=True # Mark as verified upon successful OTP
                    )
                    db.session.add(new_user)
                    db.session.flush() # IMPORTANT: This ensures new_user.id is generated before committing

                    # 2. Create and Add the Pet
                    dog_dob_date = None
                    if temp_user.get('dog_dob'):
                        try:
                            dog_dob_date = datetime.strptime(temp_user['dog_dob'], '%Y-%m-%d').date()
                        except ValueError:
                            current_app.logger.error(f"Invalid dog_dob format for {temp_user['email']}: {temp_user['dog_dob']}")
                            flash("Error with dog's date of birth format. Please try again.", 'danger')
                            db.session.rollback() # Rollback user creation as well
                            return redirect(url_for('signup'))

                    new_pet = Pet(
                        name=temp_user['dog_name'],
                        dob=dog_dob_date,
                        breed=temp_user['breed'],
                        weight=temp_user['weight'], # <-- UNCOMMENTED THIS LINE
                        owner_id=new_user.id # Link the pet to the newly created user
                    )
                    db.session.add(new_pet)

                    # 3. Commit both the new User and new Pet to the database
                    db.session.commit()
                    # --- End of User and Pet Creation ---

                    # Clean up OTP and temporary session data
                    session.pop('temp_user', None)
                    # Delete specific OTP record that was used
                    db.session.execute(db.delete(EmailOTP).where(EmailOTP.email == temp_user['email']).where(EmailOTP.otp_code == otp_entered))
                    db.session.commit() # Commit deletion of OTP

                    flash("✅ Email verified and account created successfully! Please log in.", 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback() # Rollback everything if any error occurs
                    logging.error(f"User and Pet creation error: {e}")
                    flash("Error creating your account. Please try again.", 'danger')
            else:
                flash("❌ Invalid or expired OTP. Please try again.", 'danger')
        except Exception as e:
            logging.error(f"OTP verification error: {str(e)}")
            flash("OTP verification failed due to a system error. Try again.", 'danger')

    return render_template('verify_otp.html')

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
        user = User.query.filter_by(email=email).first_or_404()
        if not user.is_email_verified:
            user.is_email_verified = True
            db.session.commit()
            flash('Email verified successfully! You can now log in.', 'success')
    except Exception as e:
        flash('Invalid or expired verification link.', 'danger')
    return redirect(url_for('login'))

# --- RESTORED LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('Email not registered. Please sign up.', 'danger')
            return redirect(url_for('signup'))
        if not check_password_hash(user.password, form.password.data):
            flash('Incorrect password.', 'danger')
            return redirect(url_for('login'))
        if not user.is_email_verified:
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('login'))

        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html', form=form)
# --- END RESTORED LOGIN ROUTE ---



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/vaccine-status')
@login_required
def vaccine_status():
    return render_template('vaccine.html')
# @app.route('/')
# def landing():
#     return render_template('landing.html')

@app.route('/map')
@login_required
def map_view():
    return render_template('index.html', Maps_key=app.config['MAP_KEY'])


if __name__ == '__main__':
    with app.app_context():
        try:
            # Check if 'mobile' column exists in 'user' table before adding
            # This is safer than just blindly creating, as it might already exist
            # You might need a more robust migration tool (like Flask-Migrate) for complex schema changes
            # db.drop_all() # <--- ADD THIS LINE TEMPORARILY
            # logging.info("⚠️ WARNING: Dropped all database tables to apply schema changes.")
            # db.create_all() # This will now recreate tables with correct names and foreign keys
            # logging.info("✅ Database tables created/updated successfully.")
            inspector = db.inspect(db.engine)
            if 'mobile' not in [column['name'] for column in inspector.get_columns('user')]:
                # Add 'mobile' column if it doesn't exist
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN mobile VARCHAR(20)'))
                db.session.commit()
                logging.info("✅ 'mobile' column added to 'user' table.")
            else:
                logging.info("✅ 'mobile' column already exists in 'user' table.")

            # Check if 'weight' column exists in 'pet' table before adding
            if 'weight' not in [column['name'] for column in inspector.get_columns('pet')]:
                # Add 'weight' column if it doesn't exist
                db.session.execute(text('ALTER TABLE "pet" ADD COLUMN weight FLOAT'))
                db.session.commit()
                logging.info("✅ 'weight' column added to 'pet' table.")
            else:
                logging.info("✅ 'weight' column already exists in 'pet' table.")

            # Removed the `DROP COLUMN username` for a cleaner start if it's already dropped.
            # If you still have a 'username' column and want to drop it, uncomment the original code
            # db.session.execute(text('ALTER TABLE "user" DROP COLUMN username'))
            # db.session.commit()
            
            db.create_all() # This creates tables that don't exist and accounts for new columns
            logging.info("✅ Database tables created/updated.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"❌ Database initialization error: {e}")
            

    app.run(debug=True, port=5000)