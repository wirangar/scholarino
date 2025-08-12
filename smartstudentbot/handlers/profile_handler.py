from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pydantic import EmailStr, ValidationError

from smartstudentbot.models import User
from smartstudentbot.utils.db_utils import get_user, save_user
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.json_utils import read_json_file

router = Router()

class EditProfileStates(StatesGroup):
    """Defines the states for the profile editing FSM."""
    field = State()
    value = State()

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return read_json_file(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Displays the user's profile information."""
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")

    if not user:
        await message.reply(lang_data.get("profile_not_found", "Please register first using /register."))
        return

    response = (
        f"*{lang_data.get('profile_info', 'Your Profile:')}*\n"
        f"*- {lang_data.get('first_name', 'First Name')}:* {user.first_name}\n"
        f"*- {lang_data.get('last_name', 'Last Name')}:* {user.last_name or '-'}\n"
        f"*- {lang_data.get('age', 'Age')}:* {user.age or '-'}\n"
        f"*- {lang_data.get('country', 'Country')}:* {user.country or '-'}\n"
        f"*- {lang_data.get('field_of_study', 'Field of Study')}:* {user.field_of_study or '-'}\n"
        f"*- {lang_data.get('email', 'Email')}:* {user.email or '-'}"
    )
    await message.reply(response, parse_mode="MarkdownV2")
    logger.info(f"User {message.from_user.id} viewed their profile.")

@router.message(Command("edit_profile"))
async def cmd_edit_profile(message: types.Message, state: FSMContext):
    """Starts the profile editing process."""
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    if not user:
        await message.reply(lang_data.get("profile_not_found", "Please register first using /register."))
        return

    fields = "`first_name`, `last_name`, `age`, `country`, `field_of_study`, `email`"
    reply_text = lang_data.get("edit_profile_field", "Which field to edit?") + f"\n{fields}"
    await message.reply(reply_text, parse_mode="MarkdownV2")
    await state.set_state(EditProfileStates.field)

@router.message(EditProfileStates.field)
async def process_edit_field(message: types.Message, state: FSMContext):
    """Processes the field to be edited and asks for the new value."""
    field = message.text.lower()
    valid_fields = ["first_name", "last_name", "age", "country", "field_of_study", "email"]
    if field not in valid_fields:
        await message.reply(f"Invalid field. Please choose one of: {', '.join(valid_fields)}")
        return

    await state.update_data(field=field)
    lang_data = load_lang() # Default to English for this prompt
    await message.reply(lang_data.get("edit_profile_value", f"Please enter the new value for `{field}`:"), parse_mode="MarkdownV2")
    await state.set_state(EditProfileStates.value)

@router.message(EditProfileStates.value)
async def process_edit_value(message: types.Message, state: FSMContext):
    """Processes the new value, validates it, and updates the user's profile."""
    data = await state.get_data()
    field = data["field"]
    value_str = message.text

    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")

    if not user:
        await message.reply(lang_data.get("profile_not_found", "Please register first using /register."))
        await state.clear()
        return

    value = value_str
    try:
        if field == "age":
            value = int(value_str)
            if not 16 <= value <= 100:
                raise ValueError("Invalid age range")
        elif field == "email":
            value = EmailStr.model_validate(value_str)
    except (ValueError, TypeError, ValidationError):
        await message.reply(f"Invalid value for `{field}`. Please try again.", parse_mode="MarkdownV2")
        return

    setattr(user, field, value)
    await save_user(user)

    success_text = lang_data.get("edit_profile_success", "Profile updated successfully!")
    await message.reply(success_text)
    logger.info(f"User {message.from_user.id} updated field: {field}")
    await state.clear()
