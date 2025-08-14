import json
from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils.localization import get_string

router = Router()

# A simple (and temporary) way to get the user's language.
# In a real application, this would come from a database or user session.
def get_user_lang(message: types.Message):
    # For now, let's assume a default. We'll need a proper way to manage this.
    # The /start command sets it, but the state is not persisted yet.
    return "en"

@router.message(Command("guide"))
async def cmd_guide(message: types.Message):
    """
    Handler for the /guide command.
    Displays the main menu for the guide.
    """
    lang = get_user_lang(message)

    builder = InlineKeyboardBuilder()

    # Dynamically create buttons for each topic in the guide
    # For now, we hardcode them based on our qna.json structure
    topics = ["housing", "transport", "university"]
    for topic in topics:
        builder.button(
            text=get_string(lang, f"guide_button_{topic}"),
            callback_data=f"guide_topic:{topic}"
        )

    builder.adjust(2) # Adjust layout to have 2 buttons per row

    await message.answer(
        text=get_string(lang, "guide_menu_title"),
        reply_markup=builder.as_markup()
    )

@router.callback_query(lambda c: c.data.startswith("guide_topic:"))
async def process_guide_topic(callback_query: types.CallbackQuery):
    """
    Handler for displaying the content of a guide topic.
    """
    lang = get_user_lang(callback_query.message)
    topic_key = callback_query.data.split(":")[1]

    # Load the guide data from qna.json
    qna_path = Path(__file__).parent.parent / "qna.json"
    with open(qna_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get the specific topic's text in the user's language
    topic_text = data.get("guide_topics", {}).get(topic_key, {}).get(lang, "Info not available.")

    # Create a "Back" button
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_string(lang, "back_button"),
        callback_data="back_to_guide_menu"
    )

    await callback_query.message.edit_text(
        text=topic_text,
        reply_markup=builder.as_markup()
    )
    await callback_query.answer()

@router.callback_query(lambda c: c.data == "back_to_guide_menu")
async def process_back_to_guide_menu(callback_query: types.CallbackQuery):
    """
    Handler for the "Back" button. Returns the user to the main guide menu.
    """
    lang = get_user_lang(callback_query.message)

    builder = InlineKeyboardBuilder()
    topics = ["housing", "transport", "university"]
    for topic in topics:
        builder.button(
            text=get_string(lang, f"guide_button_{topic}"),
            callback_data=f"guide_topic:{topic}"
        )
    builder.adjust(2)

    await callback_query.message.edit_text(
        text=get_string(lang, "guide_menu_title"),
        reply_markup=builder.as_markup()
    )
    await callback_query.answer()
