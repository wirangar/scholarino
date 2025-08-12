from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from smartstudentbot.utils.db_utils import get_user
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.json_utils import read_json_file
from smartstudentbot.config import ISEE_THRESHOLD

router = Router()

class ISEEStates(StatesGroup):
    """Defines the FSM states for the ISEE calculation process."""
    income = State()
    property_size = State()
    family_members = State()

def load_lang(lang: str = "en") -> dict:
    """Loads language strings from the correct path."""
    return read_json_file(f"smartstudentbot/lang/{lang}.json") or {}

def calculate_isee(income: float, property_size: float, family_members: int) -> tuple[float, str]:
    """Calculates the ISEE score and determines the scholarship status."""
    # Household coefficients based on the number of members
    family_coefficients = {1: 1.0, 2: 1.57, 3: 2.04, 4: 2.46, 5: 2.85}
    # For families larger than 5, the coefficient increases by 0.35 for each additional member
    coefficient = family_coefficients.get(family_members, 2.85 + (family_members - 5) * 0.35)

    # Calculate ISEE score
    property_value = property_size * 500 * 0.2
    isee = (income + property_value) / coefficient

    if ISEE_THRESHOLD <= 0: # Avoid division by zero
        percentage = 0
    else:
        percentage = (isee / ISEE_THRESHOLD) * 100

    # Determine scholarship status
    if percentage <= 55:
        status = "Full Scholarship"
    elif percentage <= 71.5:
        status = "Medium Scholarship"
    elif percentage <= 100:
        status = "Partial Scholarship"
    else:
        status = "Not Eligible"

    return isee, status

@router.message(Command("isee"))
async def cmd_isee(message: types.Message, state: FSMContext):
    """Starts the ISEE calculation process."""
    user = await get_user(message.from_user.id)
    lang = user.language if user else "en"
    lang_data = load_lang(lang)

    if not user:
        await message.reply(lang_data.get("profile_not_found", "Please register first using /register."))
        return

    await message.reply(lang_data.get("isee_income", "Please enter your total family income (in euros):"))
    await state.set_state(ISEEStates.income)

@router.message(ISEEStates.income)
async def process_income(message: types.Message, state: FSMContext):
    """Processes the income and asks for property size."""
    try:
        income = float(message.text)
        if income < 0:
            raise ValueError("Income cannot be negative")
        await state.update_data(income=income)
    except (ValueError, TypeError):
        await message.reply("Please enter a valid non-negative number for income.")
        return

    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("isee_property_size", "Please enter the property size in square meters (or 0 if none):"))
    await state.set_state(ISEEStates.property_size)

@router.message(ISEEStates.property_size)
async def process_property_size(message: types.Message, state: FSMContext):
    """Processes property size and asks for number of family members."""
    try:
        property_size = float(message.text)
        if property_size < 0:
            raise ValueError("Property size cannot be negative")
        await state.update_data(property_size=property_size)
    except (ValueError, TypeError):
        await message.reply("Please enter a valid non-negative number for property size.")
        return

    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    await message.reply(lang_data.get("isee_family_members", "Please enter the number of family members (1-10):"))
    await state.set_state(ISEEStates.family_members)

@router.message(ISEEStates.family_members)
async def process_family_members(message: types.Message, state: FSMContext):
    """Processes family members, calculates ISEE, and shows the result."""
    try:
        family_members = int(message.text)
        if not 1 <= family_members <= 10:
            raise ValueError("Invalid number of family members")

        data = await state.get_data()
        income = data["income"]
        property_size = data["property_size"]

        isee, status = calculate_isee(income, property_size, family_members)

        user = await get_user(message.from_user.id)
        lang_data = load_lang(user.language if user else "en")

        response = (
            f"{lang_data.get('isee_result', 'Your ISEE:')} {isee:.2f} €\n"
            f"{lang_data.get('isee_status', 'Scholarship Status:')} {status}"
        )
        await message.reply(response)
        logger.info(f"ISEE calculated for user {message.from_user.id}: {isee:.2f}, Status: {status}")
        await state.clear()
    except (ValueError, TypeError):
        await message.reply("Please enter a valid number for family members (between 1 and 10).")
