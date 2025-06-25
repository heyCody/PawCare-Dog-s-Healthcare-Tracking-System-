import os
import uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import psycopg2
from flask import Blueprint, request, jsonify, current_app

vaccine_bp = Blueprint('vaccine', __name__, url_prefix='/api')

# Database Configuration
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'Pawcare')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '123456')
DB_PORT = os.environ.get('DB_PORT', '5432')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# Standard Vaccine Schedule
STANDARD_VACCINE_SCHEDULE = [
    {"id": "dhpp-1", "name": "DHPP-1", "type": "PUPPY", "initial_age_weeks": 8, "booster_interval_months": None, "notes": "Distemper, Hepatitis, Parvovirus, Parainfluenza"},
    {"id": "dhpp-2", "name": "DHPP-2", "type": "PUPPY", "initial_age_weeks": 12, "booster_interval_months": None, "notes": "Booster for DHPP-1"},
    {"id": "dhpp-3", "name": "DHPP-3", "type": "PUPPY", "initial_age_weeks": 16, "booster_interval_months": 12, "notes": "Final puppy DHPP, then annual booster"},
    {"id": "rabies-1", "name": "Rabies", "type": "PUPPY", "initial_age_weeks": 16, "booster_interval_months": 12, "notes": "First Rabies shot"},
    {"id": "lepto-1", "name": "Leptospirosis-1", "type": "PUPPY", "initial_age_weeks": 16, "booster_interval_months": None, "notes": "First Lepto shot"},
    {"id": "lepto-2", "name": "Leptospirosis-2", "type": "PUPPY", "initial_age_weeks": 20, "booster_interval_months": 12, "notes": "Second Lepto shot"},
    {"id": "bordetella", "name": "Bordetella", "type": "ANNUAL", "initial_age_weeks": None, "booster_interval_months": 12, "notes": "Kennel Cough"},
]

@vaccine_bp.route('/dog_vaccine_data', methods=['GET'])
def get_dog_vaccine_dashboard():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Optional: filter by owner_id if needed
        owner_id = request.args.get("owner_id")
        if owner_id:
            cur.execute("SELECT id, name, dob FROM Pet WHERE owner_id = %s ORDER BY id DESC LIMIT 1", (owner_id,))
        else:
            cur.execute("SELECT id, name, dob FROM Pet ORDER BY id DESC LIMIT 1")

        dog = cur.fetchone()
        if not dog:
            return jsonify({
                "dog_name": "No Dog Found",
                "dog_dob": "N/A",
                "schedule": [],
                "history": []
            })

        dog_id, dog_name, dog_dob = dog
        today = date.today()
        one_year_later = today + timedelta(days=365)

        # Fetch vaccination history: actual dates given
        cur.execute("""
    SELECT vaccine_name, vaccine_date 
    FROM vaccination 
    WHERE pet_id = %s 
      AND next_due_date <= %s
    ORDER BY next_due_date ASC
""", (dog_id, one_year_later))

        records = cur.fetchall()
        given_map = {name: vaccine_date for name, vaccine_date in records}


        history = []
        schedule = []

        for vaccine in STANDARD_VACCINE_SCHEDULE:
            name = vaccine["name"]
            booster = vaccine["booster_interval_months"]
            given_date = given_map.get(name)

            if given_date:
                # Add to history
                history.append({
                    "vaccine": name,
                    "date_given": given_date.isoformat()
                })

                # Calculate next booster if applicable
                if booster:
                    next_due = given_date + relativedelta(months=booster)
                    if next_due >= today:
                        schedule.append({
                            "vaccine": f"{name} (Booster Due)" if next_due <= today else name,
                            "due_date": next_due.isoformat(),
                            "notes": vaccine["notes"]
                        })

            else:
                # Not yet given → compute expected due date
                if vaccine["type"] == "PUPPY" and vaccine["initial_age_weeks"] is not None:
                    expected = dog_dob + timedelta(weeks=vaccine["initial_age_weeks"])
                    if expected >= today or expected + timedelta(days=90) >= today:  # reasonable window
                        label = f"{name} (Pending/Overdue)" if expected < today else name
                        schedule.append({
                            "vaccine": label,
                            "due_date": expected.isoformat(),
                            "notes": vaccine["notes"]
                        })
                elif vaccine["type"] == "ANNUAL":
                    age_in_years = (today - dog_dob).days / 365.25
                    due_date = today if age_in_years >= 1 else dog_dob + relativedelta(years=1)
                    if due_date >= today:
                        label = f"{name} (Annual Due)" if due_date <= today else name
                        schedule.append({
                            "vaccine": label,
                            "due_date": due_date.isoformat(),
                            "notes": vaccine["notes"]
                        })

        # Sort by date
        schedule.sort(key=lambda x: x["due_date"])
        history.sort(key=lambda x: x["date_given"], reverse=True)

        return jsonify({
            "dog_name": dog_name,
            "dog_dob": dog_dob.isoformat(),
            "schedule": schedule,
            "history": history
        })

    except Exception as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify({"message": "Internal server error"}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()
