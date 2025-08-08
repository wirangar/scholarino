from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from smartstudentbot.utils.db_utils import get_user
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version
from smartstudentbot.config import ADMIN_CHAT_IDS

router = Router()

class ConsultationStates(StatesGroup):
    """Defines the FSM states for the consultation form."""
    name = State()
    field_of_study = State()
    gpa = State()
    budget = State()
    language_level = State()
    # resume = State() # For a future step, to handle file uploads

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return check_json_version(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("consult"))
async def cmd_consult(message: types.Message, state: FSMContext):
    """Starts the academic consultation process."""
    user = await get_user(message.from_user.id)
    lang = user.language if user else "en"
    lang_data = load_lang(lang)

    if not user:
        await message.reply(lang_data.get("profile_not_found", "Please register first using /register."))
        return

    await message.reply(lang_data.get("consult_name", "Let's start the consultation process. What is your full name?"))
    await state.set_state(ConsultationStates.name)
    logger.info(f"User {message.from_user.id} started consultation process.")

@router.message(ConsultationStates.name)
async def process_consult_name(message: types.Message, state: FSMContext):
    """Processes the user's name and asks for their desired field of study."""
    await state.update_data(name=message.text)
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("consult_field", "Which field of study are you interested in?"))
    await state.set_state(ConsultationStates.field_of_study)

@router.message(ConsultationStates.field_of_study)
async def process_consult_field(message: types.Message, state: FSMContext):
    """Processes the field of study and asks for GPA."""
    await state.update_data(field_of_study=message.text)
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("consult_gpa", "What is your current GPA (Grade Point Average)?"))
    await state.set_state(ConsultationStates.gpa)

@router.message(ConsultationStates.gpa)
async def process_consult_gpa(message: types.Message, state: FSMContext):
    """Processes the GPA and asks for the budget."""
    await state.update_data(gpa=message.text)
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("consult_budget", "What is your approximate budget for tuition per year (in euros)?"))
    await state.set_state(ConsultationStates.budget)

@router.message(ConsultationStates.budget)
async def process_consult_budget(message: types.Message, state: FSMContext):
    """Processes the budget and asks for language level."""
    try:
        budget = float(message.text)
        await state.update_data(budget=budget)
    except (ValueError, TypeError):
        await message.reply("Please enter a valid number for your budget.")
        return
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("consult_language", "What is your current Italian/English language proficiency level (e.g., A2, B1, C1)?"))
    await state.set_state(ConsultationStates.language_level)

async def notify_admins(bot: Bot, user: types.User, form_data: dict):
    """Formats and sends the consultation data to all admins."""
    admin_message = (
        f"New Consultation Request from User ID: {user.id} (@{user.username})\n"
        f"-----------------------------------------\n"
        f"Full Name: {form_data.get('name')}\n"
        f"Desired Field: {form_data.get('field_of_study')}\n"
        f"GPA: {form_data.get('gpa')}\n"
        f"Budget: {form_data.get('budget')} EUR\n"
        f"Language Level: {form_data.get('language_level')}\n"
        f"-----------------------------------------"
    )
    for admin_id in ADMIN_CHAT_IDS:
        if not admin_id: continue
        try:
            await bot.send_message(admin_id, admin_message)
            logger.info(f"Consultation form for user {user.id} sent to admin {admin_id}.")
        except Exception as e:
            logger.error(f"Failed to send consultation form to admin {admin_id}: {e}")

@router.message(ConsultationStates.language_level)
async def process_consult_language(message: types.Message, state: FSMContext, bot: Bot):
    """Processes the language level, notifies admins, and concludes the form."""
    await state.update_data(language_level=message.text)
    form_data = await state.get_data()

    # Send the collected data to all admins
    await notify_admins(bot, message.from_user, form_data)

    # Confirm completion to the user
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")

    summary = (
        f"Thank you! Your consultation request has been submitted.\n"
        f"An admin will review your request and get back to you soon."
    )

    await message.reply(lang_data.get("consult_success", summary))
    logger.info(f"User {message.from_user.id} completed consultation form.")
    await state.clear()
