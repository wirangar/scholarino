import os
from datetime import time
from dotenv import load_dotenv

load_dotenv()

BOT_ID = os.getenv("BOT_ID", "perugia")
CITY_NAME = os.getenv("CITY_NAME", "Perugia")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YourChannel")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
# Default to an in-memory SQLite database for testing and local runs.
# The production environment can override this with a file path.
SQLITE_DB = os.getenv("SQLITE_DB", ":memory:")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")
GOOGLE_DRIVE_CREDS = os.getenv("GOOGLE_DRIVE_CREDS")
GOOGLE_DRIVE_UPLOAD_FOLDER_ID = os.getenv("GOOGLE_DRIVE_UPLOAD_FOLDER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SHEET_ID = os.getenv("SHEET_ID")
QUESTIONS_SHEET_NAME = os.getenv("QUESTIONS_SHEET_NAME", "SmartStudentBotQuestions")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Scholarship")
PORT = int(os.getenv("PORT", 8000))
JSON_VERSION = os.getenv("JSON_VERSION", "1.0")
FEATURE_FLAGS = {
    "GAMIFICATION": True,
    "PODCASTS": True,
    "ROOMMATE": True,
    "NEWS": True
}
ADMIN_WORKING_HOURS = (time(9, 0), time(17, 0))
ISEE_THRESHOLD = 23000
ADMIN_DASHBOARD_PASSWORD = os.getenv("ADMIN_DASHBOARD_PASSWORD", "strongpassword123")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "a_very_secret_key_for_session")
