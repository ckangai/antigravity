import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from google.cloud.sql.connector import Connector, IPTypes

# Initialize Flask app
app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev_key")  # Change for production

# Database Configuration
# These environment variables must be set in Cloud Run
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")

# Email Configuration
# Email Configuration
EMAIL_USER = os.environ.get("EMAIL_USER", "charles@theittrainingacademy.com")
# Support both generic EMAIL_PASSWORD and the previous GMAIL_APP_PASSWORD variable
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD", os.environ.get("GMAIL_APP_PASSWORD", "")).replace(" ", "")

# Debug Credentials (Masked)
logger.info(f"Configured EMAIL_USER: '{EMAIL_USER}'")
if EMAIL_PASS:
    logger.info(f"EMAIL_PASS configured. Length: {len(EMAIL_PASS)}")
    # Log first/last chars to check for accidental quotes
    logger.info(f"EMAIL_PASS starts with: '{EMAIL_PASS[:1]}', ends with: '{EMAIL_PASS[-1:]}'")
else:
    logger.warning("EMAIL_PASS is empty or not set.")

# SQLAlchemy Setup
Base = declarative_base()

class CityEntry(Base):
    __tablename__ = "city_entries"
    id = Column(Integer, primary_key=True)
    city = Column(String(255), nullable=False)
    specialty = Column(Text, nullable=False)
    user_email = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database Connection Helper
def getconn():
    with Connector() as connector:
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pymysql",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            ip_type=IPTypes.PUBLIC,  # Use PRIVATE for VPC
        )
        return conn

def init_db():
    # Helper to initialize DB (create tables)
    # In production, use migrations (Alembic) or manual schema creation
    # This is a basic setup to ensure tables exist if variables are set
    if INSTANCE_CONNECTION_NAME and DB_USER:
        pool = create_engine(
            "mysql+pymysql://",
            creator=getconn,
        )
        # Note: This might not update existing tables with new columns. 
        # Use proper migrations for schema changes.
        Base.metadata.create_all(pool)
        return sessionmaker(bind=pool)
    return None

# Global Session Factory
Session = None
try:
    if INSTANCE_CONNECTION_NAME:
        Session = init_db()
except Exception as e:
    logging.error(f"Failed to initialize database: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form.get("city")
        specialty = request.form.get("specialty")
        user_email = request.form.get("user_email")

        if not city or not specialty or not user_email:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("index"))

        # 1. Save to Database
        if Session:
            try:
                session = Session()
                new_entry = CityEntry(city=city, specialty=specialty, user_email=user_email)
                session.add(new_entry)
                session.commit()
                session.close()
            except Exception as e:
                logging.error(f"Database error: {e}")
                flash("Error saving to database. Check logs.", "error")
        else:
            logging.warning("Database not configured. Skipping save.")

        # 2. Send Email
        if EMAIL_PASS:
            logger.info("Email password configured. Attempting to send emails.")
            try:
                # Send to Admin
                logger.info("Sending notification to admin...")
                send_email("charles@charleskangai.co.uk", city, specialty, user_email)
                # Send to User
                logger.info(f"Sending confirmation to user {user_email}...")
                send_email(user_email, city, specialty, user_email)
            except Exception as e:
                logger.error(f"Top-level email error: {e}")
                flash("Entry saved, but failed to send email. Check server logs for details.", "warning")
        else:
             logger.warning("Email password (EMAIL_PASSWORD) not configured. Skipping email.")

        flash(f"Success! {city} added.", "success")
        return redirect(url_for("index"))

    return render_template("index.html")

def send_email(to_email, city, specialty, user_email):
    try:
        logger.info(f"Preparing to send email to: {to_email}")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = "New City Record"

        body = f"A new record has been added:\n\nCity: {city}\nSpecialty: {specialty}\nSubmitted by: {user_email}"
        msg.attach(MIMEText(body, "plain"))

        logger.info("Connecting to SMTP server (mail.theittrainingacademy.com:465)...")
        # Use SMTP_SSL for port 465
        server = smtplib.SMTP_SSL("mail.theittrainingacademy.com", 465)
        
        # Note: server.starttls() is NOT needed for SMTP_SSL (port 465), connection is secure from start
        
        logger.info(f"Logging in as {EMAIL_USER}...")
        server.login(EMAIL_USER, EMAIL_PASS)
        
        logger.info("Sending message...")
        server.send_message(msg)
        
        logger.info("Quitting server...")
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        logger.exception(f"Failed to send email to {to_email}. Error: {e}")
        raise e  # Re-raise to be caught by the caller if needed

if __name__ == "__main__":
    # Local development
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
