import os
from datetime import time

BOT_ID = os.getenv("BOT_ID", "perugia")
CITY_NAME = os.getenv("CITY_NAME", "Perugia")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "7801271819").split(",")
ADMIN_ROLES = {id: "OWNER" if id == "7801271819" else "ADMIN" for id in ADMIN_CHAT_IDS}
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YourChannel")
BASE_URL = os.getenv("BASE_URL", "https://example.com")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "a_very_secret_string")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
SQLITE_DB = os.getenv("SQLITE_DB", "data.db")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")
GOOGLE_DRIVE_CREDS = os.getenv("GOOGLE_DRIVE_CREDS")
GOOGLE_DRIVE_UPLOAD_FOLDER_ID = os.getenv("GOOGLE_DRIVE_UPLOAD_FOLDER_ID")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SHEET_ID = os.getenv("SHEET_ID")
QUESTIONS_SHEET_NAME = os.getenv("QUESTIONS_SHEET_NAME", "StudentBotQuestions")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Scholarship")
JSON_VERSION = "1.0"
FEATURE_FLAGS = {
    "GAMIFICATION": True,
    "PODCASTS": True,
    "ROOMMATE": True,
    "NEWS": True,
    "AI": True
}
ISEE_THRESHOLD = 23000 # Added from another part of the prompt for the ISEE calculation example
