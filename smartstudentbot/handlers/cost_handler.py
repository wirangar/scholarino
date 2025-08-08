from aiogram import Router, types
from aiogram.filters import Command

from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version
from smartstudentbot.utils.db_utils import get_user

router = Router()

COST_OF_LIVING_PATH = "smartstudentbot/cost_of_living.json"

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return check_json_version(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("cost"))
async def cost_of_living_handler(message: types.Message):
    """
    Displays the estimated cost of living in the city, using internationalized strings.
    """
    logger.info(f"User {message.from_user.id} requested cost of living information.")

    user = await get_user(message.from_user.id)
    lang = user.language if user else "en"
    lang_data = load_lang(lang)

    data = check_json_version(COST_OF_LIVING_PATH)

    if not data:
        await message.reply(lang_data.get("cost_of_living_no_data", "Sorry, I couldn't retrieve the cost of living information at the moment."))
        return

    city = data.get('city', 'the city')
    currency = data.get('currency', 'EUR')
    summary = data.get('summary', '')
    categories = data.get('categories', [])

    title = lang_data.get("cost_of_living_title", "Estimated Cost of Living in {city}").format(city=city)
    response = f"📊 *{title}* 📊\n\n"

    if summary:
        response += f"_{summary}_\n\n"

    response += lang_data.get("cost_of_living_breakdown", "Here is a breakdown of average monthly expenses:") + "\n\n"

    for category in categories:
        name = category.get('name', 'N/A')
        cost = category.get('average_cost', 'N/A')
        description = category.get('description', '')
        # Using MarkdownV2 requires escaping special characters
        response += f"🔹 *{name.replace('-', ' ')}:* {cost} {currency}\n"
        response += f"   _{description.replace('.', '\\.')}_\n\n"

    await message.reply(response, parse_mode="MarkdownV2")
