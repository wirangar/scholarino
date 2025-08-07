from aiogram import Router, types
from aiogram.filters import Command
import json
import os

# Assuming the script is run from the repository root
LANG_DIR = "smartstudentbot/lang"

# A more robust way to get the logger from the utils module
try:
    from utils.logger import logger
except ImportError:
    from smartstudentbot.utils.logger import logger

router = Router()

def load_lang(lang: str = "en"):
    """Loads the language file for the given language code."""
    file_path = os.path.join(LANG_DIR, f"{lang}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Language file not found for lang='{lang}' at {file_path}")
        # Fallback to English if the requested language is not found
        if lang != "en":
            return load_lang("en")
        return {"welcome_message": "Welcome (language file missing)."}
    except json.JSONDecodeError:
        logger.error(f"Could not decode language file for lang='{lang}' at {file_path}")
        return {"welcome_message": "Welcome (language file corrupted)."}


@router.message(Command("start"))
async def cmd_start_handler(message: types.Message):
    """Handles the /start command."""
    # For now, we default to English. Language selection will be implemented later.
    user_lang = "en"
    lang_data = load_lang(user_lang)

    welcome_msg = lang_data.get("welcome_message", "Welcome to SmartStudentBot!")

    await message.reply(welcome_msg)
    logger.info(f"User {message.from_user.id} started the bot.")
