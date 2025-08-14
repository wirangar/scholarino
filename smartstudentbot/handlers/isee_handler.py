from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..utils.localization import get_string

# Define the states for the ISEE calculation form
class IseeForm(StatesGroup):
    awaiting_income = State()
    awaiting_property = State()
    awaiting_family_members = State()

router = Router()

# A temporary way to get user language
def get_user_lang(message: types.Message):
    return "en"

@router.message(Command("isee"))
async def cmd_isee_start(message: types.Message, state: FSMContext):
    """
    Starts the ISEE calculation form.
    """
    lang = get_user_lang(message)
    await message.answer(get_string(lang, "isee_intro"))
    await message.answer(get_string(lang, "ask_income"))
    await state.set_state(IseeForm.awaiting_income)

@router.message(IseeForm.awaiting_income)
async def process_income(message: types.Message, state: FSMContext):
    """
    Processes the user's income and asks for property size.
    """
    lang = get_user_lang(message)
    try:
        income = float(message.text)
        await state.update_data(income=income)
        await message.answer(get_string(lang, "ask_property"))
        await state.set_state(IseeForm.awaiting_property)
    except (ValueError, TypeError):
        await message.answer(get_string(lang, "invalid_input"))

@router.message(IseeForm.awaiting_property)
async def process_property(message: types.Message, state: FSMContext):
    """
    Processes the property size and asks for family members.
    """
    lang = get_user_lang(message)
    try:
        property_size = float(message.text)
        await state.update_data(property_size=property_size)
        await message.answer(get_string(lang, "ask_family_members"))
        await state.set_state(IseeForm.awaiting_family_members)
    except (ValueError, TypeError):
        await message.answer(get_string(lang, "invalid_input"))

def get_family_coefficient(member_count: int) -> float:
    """
    Returns the family coefficient based on the number of members.
    This is a simplified mapping based on the prompt's examples.
    """
    coefficients = {1: 1.0, 2: 1.57, 3: 2.04, 4: 2.46, 5: 2.85}
    return coefficients.get(member_count, 2.85 + (0.35 * (member_count - 5)))

def calculate_scholarship_status(isee: float, lang: str) -> str:
    """
    Determines the scholarship status based on the calculated ISEE value.
    The threshold is hardcoded as per the prompt, but should be in config.
    """
    ISEE_THRESHOLD = 23000.0
    percentage = (isee / ISEE_THRESHOLD) * 100

    if percentage <= 55:
        return get_string(lang, "scholarship_status_full")
    elif percentage <= 71.5:
        return get_string(lang, "scholarship_status_medium")
    elif percentage <= 100:
        return get_string(lang, "scholarship_status_partial")
    else:
        return get_string(lang, "scholarship_status_none")

@router.message(IseeForm.awaiting_family_members)
async def process_family_members(message: types.Message, state: FSMContext):
    """
    Processes the final piece of data, calculates the ISEE, and shows the result.
    """
    lang = get_user_lang(message)
    try:
        family_members = int(message.text)
        await state.update_data(family_members=family_members)

        # Get all data from FSM context
        user_data = await state.get_data()
        income = user_data.get("income", 0.0)
        property_size = user_data.get("property_size", 0.0)

        # Calculate ISEE
        property_value = property_size * 500
        family_coefficient = get_family_coefficient(family_members)

        if family_coefficient == 0: # Avoid division by zero
             await message.answer("Family coefficient cannot be zero.")
             await state.clear()
             return

        isee_value = (income + (property_value * 0.2)) / family_coefficient

        # Determine scholarship status
        status = calculate_scholarship_status(isee_value, lang)

        # Send the result to the user
        result_text = get_string(lang, "isee_result_message").format(isee=isee_value, status=status)
        await message.answer(result_text)

        # Clear the state, ending the conversation
        await state.clear()

    except (ValueError, TypeError):
        await message.answer(get_string(lang, "invalid_input"))


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """
    Allows the user to cancel any action at any time.
    """
    lang = get_user_lang(message)
    current_state = await state.get_state()
    if current_state is None:
        return # No active state to cancel

    await state.clear()
    await message.answer(get_string(lang, "calculation_cancelled"))
