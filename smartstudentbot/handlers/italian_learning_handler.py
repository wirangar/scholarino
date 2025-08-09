from aiogram import Router, types
from aiogram.filters import Command

from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version
from smartstudentbot.utils.db_utils import get_user

router = Router()

RESOURCES_PATH = "smartstudentbot/italian_learning_resources.json"

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return check_json_version(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("italian"))
async def italian_learning_handler(message: types.Message):
    """
    Displays resources for learning the Italian language.
    """
    logger.info(f"User {message.from_user.id} requested Italian learning resources.")

    user = await get_user(message.from_user.id)
    lang = user.language if user else "en"
    lang_data = load_lang(lang)

    data = check_json_version(RESOURCES_PATH)

    if not data or not data.get("data"):
        await message.reply(lang_data.get("italian_resources_no_data", "Sorry, I couldn't find any language learning resources right now."))
        return

    response = lang_data.get("italian_resources_title", "🇮🇹 **Italian Learning Resources** 🇮🇹") + "\n\n"

    for resource in data["data"]:
        name = resource.get('name', 'N/A')
        res_type = resource.get('type', 'N/A')
        description = resource.get('description', '')
        link = resource.get('link')

        response += f"🔹 **{name}** ({res_type})\n"
        response += f"   _{description}_\n"
        if link:
            response += f"   [Go to Resource]({link})\n"
        response += "\n"

    await message.reply(response, parse_mode="Markdown", disable_web_page_preview=True)
