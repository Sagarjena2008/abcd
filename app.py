import logging
import os
import re
from datetime import date
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from mysql.connector import Error as MySQLError


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
logging.basicConfig(level=logging.INFO)

ALLOWED_PLANS = {"Monthly", "Quarterly", "Half-yearly", "Yearly", "Trial session"}
ALLOWED_TIMES = {"Morning", "Afternoon", "Evening", "Flexible"}
PHONE_PATTERN = re.compile(r"^[0-9+() .-]{8,20}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db_connection():
    password = os.getenv("MYSQL_PASSWORD")
    if not password:
        raise RuntimeError("MYSQL_PASSWORD is not set. Add it to the .env file.")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "gymkhana_app"),
        password=password,
        database=os.getenv("MYSQL_DATABASE", "gymkhana"),
        connection_timeout=5,
    )


def validate_registration(data):
    if not isinstance(data, dict):
        return None, "Submit registration details as JSON."

    full_name = data.get("fullName")
    email = data.get("email")
    phone = data.get("phone")
    plan = data.get("plan")
    start_date = data.get("startDate") or None
    preferred_time = data.get("preferredTime")
    goals = data.get("goals") or ""

    if not all(isinstance(value, str) for value in (full_name, email, phone, plan, preferred_time, goals)):
        return None, "One or more fields have an invalid value."
    full_name, email, phone = full_name.strip(), email.strip().lower(), phone.strip()
    goals = goals.strip()
    if not full_name or len(full_name) > 80:
        return None, "Enter a name of 1 to 80 characters."
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        return None, "Enter a valid email address."
    if not PHONE_PATTERN.fullmatch(phone):
        return None, "Enter a phone number using 8 to 20 digits or phone symbols."
    if plan not in ALLOWED_PLANS:
        return None, "Choose a valid membership plan."
    if preferred_time not in ALLOWED_TIMES:
        return None, "Choose a valid preferred workout time."
    if len(goals) > 500:
        return None, "Fitness goals must be 500 characters or fewer."
    if data.get("consent") is not True:
        return None, "Consent is required before submitting your registration."
    if start_date:
        if not isinstance(start_date, str):
            return None, "Choose a valid start date."
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            return None, "Choose a valid start date."

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "plan": plan,
        "start_date": start_date,
        "preferred_time": preferred_time,
        "goals": goals,
    }, None


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/registrations/count")
def registration_count():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        cursor.close()
        return jsonify(count=count)
    except (MySQLError, RuntimeError, ValueError):
        app.logger.exception("Could not read registration count")
        return jsonify(error="Registration totals are temporarily unavailable."), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.post("/api/registrations")
def create_registration():
    registration, error = validate_registration(request.get_json(silent=True))
    if error:
        return jsonify(error=error), 400

    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO registrations
                (full_name, email, phone, plan, start_date, preferred_time, goals, consent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                registration["full_name"],
                registration["email"],
                registration["phone"],
                registration["plan"],
                registration["start_date"],
                registration["preferred_time"],
                registration["goals"] or None,
                True,
            ),
        )
        connection.commit()
        registration_id = cursor.lastrowid
        cursor.close()
        return jsonify(id=registration_id, message="Registration saved."), 201
    except (MySQLError, RuntimeError, ValueError):
        app.logger.exception("Could not save a registration")
        if connection and connection.is_connected():
            connection.rollback()
        return jsonify(error="Your registration could not be saved right now. Please try again."), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(host=os.getenv("APP_HOST", "127.0.0.1"), port=int(os.getenv("APP_PORT", "5000")))
