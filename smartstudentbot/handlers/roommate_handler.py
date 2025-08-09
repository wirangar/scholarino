from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from smartstudentbot.models import RoommatePreferences
from smartstudentbot.utils.db_utils import get_user, save_user
from smartstudentbot.utils.logger import logger

router = Router()

class RoommateStates(StatesGroup):
    """Defines the FSM states for finding a roommate."""
    looking = State()
    budget = State()
    smoker = State()
    notes = State()

@router.message(Command("roommate"))
async def cmd_roommate(message: types.Message, state: FSMContext):
    """Starts the roommate preference setup process."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.reply("Please register with /register first.")
        return

    await message.reply("Are you currently looking for a roommate? (yes/no)")
    await state.set_state(RoommateStates.looking)

@router.message(RoommateStates.looking)
async def process_looking(message: types.Message, state: FSMContext):
    """Processes whether the user is looking for a roommate."""
    is_looking = message.text.lower()
    if is_looking not in ['yes', 'no']:
        await message.reply("Please answer with 'yes' or 'no'.")
        return

    user = await get_user(message.from_user.id)
    user.roommate_prefs.looking_for_roommate = (is_looking == 'yes')

    if not user.roommate_prefs.looking_for_roommate:
        await save_user(user)
        await message.reply("Your roommate search status has been updated. You are not currently looking.")
        await state.clear()
        return

    await message.reply("What is your monthly budget for rent? (e.g., 250-350)")
    await state.set_state(RoommateStates.budget)

@router.message(RoommateStates.budget)
async def process_budget(message: types.Message, state: FSMContext):
    """Processes the user's budget."""
    try:
        budget_min, budget_max = map(int, message.text.split('-'))
        await state.update_data(budget_min=budget_min, budget_max=budget_max)
    except ValueError:
        await message.reply("Please provide the budget as a range, e.g., '250-350'.")
        return

    await message.reply("Do you smoke? (yes/no)")
    await state.set_state(RoommateStates.smoker)

@router.message(RoommateStates.smoker)
async def process_smoker(message: types.Message, state: FSMContext):
    """Processes smoking preference."""
    is_smoker = message.text.lower()
    if is_smoker not in ['yes', 'no']:
        await message.reply("Please answer with 'yes' or 'no'.")
        return
    await state.update_data(smoker=(is_smoker == 'yes'))

    await message.reply("Any additional notes about yourself or what you're looking for? (e.g., 'I'm a quiet person, looking for a clean apartment')")
    await state.set_state(RoommateStates.notes)

@router.message(RoommateStates.notes)
async def process_notes(message: types.Message, state: FSMContext):
    """Processes notes and finalizes the preferences."""
    form_data = await state.get_data()
    user = await get_user(message.from_user.id)

    user.roommate_prefs.budget_min = form_data.get("budget_min")
    user.roommate_prefs.budget_max = form_data.get("budget_max")
    user.roommate_prefs.smoker = form_data.get("smoker")
    user.roommate_prefs.notes = message.text

    await save_user(user)
    await message.reply("Your roommate preferences have been saved! You can now be found by other students.")
    logger.info(f"User {message.from_user.id} updated roommate preferences.")
    await state.clear()
