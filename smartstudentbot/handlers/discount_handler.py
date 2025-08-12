from aiogram import Router, types
from aiogram.filters import Command

from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.json_utils import read_json_file
from smartstudentbot.utils.db_utils import get_user

router = Router()

DISCOUNTS_PATH = "smartstudentbot/discounts.json"

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return read_json_file(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("discounts"))
async def discounts_handler(message: types.Message):
    """
    Displays available student discounts.
    """
    logger.info(f"User {message.from_user.id} requested student discounts.")

    user = await get_user(message.from_user.id)
    lang = user.language if user else "en"
    lang_data = load_lang(lang)

    data = read_json_file(DISCOUNTS_PATH)

    if not data or not data.get("data"):
        await message.reply(lang_data.get("discounts_no_data", "Sorry, I couldn't find any discount information right now."))
        return

    response = lang_data.get("discounts_title", "💸 **Student Discounts** 💸") + "\n\n"

    for discount in data["data"]:
        name = discount.get('name', 'N/A')
        category = discount.get('category', 'N/A')
        description = discount.get('description', '')
        link = discount.get('link')

        response += f"🔹 **{name}** ({category})\n"
        response += f"   _{description}_\n"
        if link:
            response += f"   [More Info]({link})\n"
        response += "\n"

    await message.reply(response, parse_mode="Markdown", disable_web_page_preview=True)
