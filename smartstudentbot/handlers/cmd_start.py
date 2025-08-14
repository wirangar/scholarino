from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..utils.localization import get_string

# All handlers for the bot should be defined in routers
router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Handler for the /start command.
    Greets the user and offers language selection.
    """
    # We will use 'en' as the default language for the initial welcome message.
    # The user's selected language will be stored later (e.g., in a database or FSM).
    lang_code = "en"

    # Build the inline keyboard for language selection
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=get_string(lang_code, "lang_button_en"),
        callback_data="set_lang:en"
    )
    keyboard.button(
        text=get_string(lang_code, "lang_button_fa"),
        callback_data="set_lang:fa"
    )
    keyboard.button(
        text=get_string(lang_code, "lang_button_it"),
        callback_data="set_lang:it"
    )
    # Adjust the layout to have buttons side-by-side if possible
    keyboard.adjust(3)

    await message.answer(
        text=get_string(lang_code, "welcome"),
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(lambda c: c.data.startswith("set_lang:"))
async def process_language_selection(callback_query: types.CallbackQuery):
    """
    Handler for the language selection callback.
    Sets the user's language and confirms the selection.
    """
    lang_code = callback_query.data.split(":")[1]

    # Here you would typically save the user's language preference.
    # For now, we will just send a confirmation message in the selected language.
    # For example: await db.set_user_language(user_id=callback_query.from_user.id, lang_code=lang_code)

    confirmation_text = get_string(lang_code, "language_selected")

    await callback_query.message.edit_text(
        text=confirmation_text,
        reply_markup=None  # Remove the keyboard after selection
    )
    await callback_query.answer() # Acknowledge the callback query
