from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pydantic import EmailStr, ValidationError

from smartstudentbot.models import User
from smartstudentbot.utils.db_utils import save_user
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.json_utils import read_json_file
from smartstudentbot.utils.gamification import award_points_for_action

router = Router()

class RegisterStates(StatesGroup):
    """Defines the states for the user registration FSM."""
    first_name = State()
    last_name = State()
    age = State()
    country = State()
    field_of_study = State()
    email = State()

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    # Corrected path to be relative to the project root
    return read_json_file(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    """Starts the registration process."""
    lang_data = load_lang() # Defaults to 'en'
    await message.reply(lang_data.get("register_first_name", "Please enter your first name:"))
    await state.set_state(RegisterStates.first_name)

@router.message(RegisterStates.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    """Processes the first name and asks for the last name."""
    await state.update_data(first_name=message.text)
    lang_data = load_lang()
    await message.reply(lang_data.get("register_last_name", "Please enter your last name (or type /skip):"))
    await state.set_state(RegisterStates.last_name)

@router.message(RegisterStates.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    """Processes the last name and asks for age."""
    if message.text.lower() != "/skip":
        await state.update_data(last_name=message.text)
    lang_data = load_lang()
    await message.reply(lang_data.get("register_age", "Please enter your age (or type /skip):"))
    await state.set_state(RegisterStates.age)

@router.message(RegisterStates.age)
async def process_age(message: types.Message, state: FSMContext):
    """Processes age and asks for country."""
    if message.text.lower() != "/skip":
        try:
            age = int(message.text)
            if not 16 <= age <= 100:
                raise ValueError("Invalid age range")
            await state.update_data(age=age)
        except (ValueError, TypeError):
            await message.reply("Please enter a valid number for age (between 16 and 100), or type /skip.")
            return
    lang_data = load_lang()
    await message.reply(lang_data.get("register_country", "Please enter your country (or type /skip):"))
    await state.set_state(RegisterStates.country)

@router.message(RegisterStates.country)
async def process_country(message: types.Message, state: FSMContext):
    """Processes country and asks for field of study."""
    if message.text.lower() != "/skip":
        await state.update_data(country=message.text)
    lang_data = load_lang()
    await message.reply(lang_data.get("register_field_of_study", "Please enter your field of study (or type /skip):"))
    await state.set_state(RegisterStates.field_of_study)

@router.message(RegisterStates.field_of_study)
async def process_field_of_study(message: types.Message, state: FSMContext):
    """Processes field of study and asks for email."""
    if message.text.lower() != "/skip":
        await state.update_data(field_of_study=message.text)
    lang_data = load_lang()
    await message.reply(lang_data.get("register_email", "Please enter your email (or type /skip):"))
    await state.set_state(RegisterStates.email)

@router.message(RegisterStates.email)
async def process_email(message: types.Message, state: FSMContext):
    """Processes email, finalizes registration, and saves the user."""
    data = await state.get_data()
    email_to_validate = message.text

    if email_to_validate.lower() != "/skip":
        try:
            # Pydantic's EmailStr is a class, not a function. We can use it for validation.
            _ = EmailStr.model_validate(email_to_validate)
            await state.update_data(email=email_to_validate)
        except ValidationError:
            await message.reply("Please enter a valid email address, or type /skip.")
            return

    # We need to refresh the data after the potential update
    final_data = await state.get_data()

    user_model = User(
        user_id=message.from_user.id,
        first_name=final_data["first_name"],
        last_name=final_data.get("last_name"),
        age=final_data.get("age"),
        country=final_data.get("country"),
        field_of_study=final_data.get("field_of_study"),
        email=final_data.get("email")
    )

    await save_user(user_model)

    # Award points for completing registration
    await award_points_for_action(message.from_user.id, "complete_registration")

    lang_data = load_lang()
    await message.reply(lang_data.get("register_success", "Registration successful! Thank you."))
    logger.info(f"User {message.from_user.id} completed registration.")
    await state.clear()
