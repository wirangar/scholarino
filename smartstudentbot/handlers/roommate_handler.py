from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from smartstudentbot.models import RoommatePreferences
from smartstudentbot.utils.db_utils import get_user, save_user, find_matching_roommates
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version

router = Router()

class RoommateStates(StatesGroup):
    looking = State()
    budget = State()
    smoker = State()
    notes = State()

def load_lang(lang: str = "en") -> dict:
    return check_json_version(f"smartstudentbot/lang/{lang}.json") or {}

@router.message(Command("roommate"))
async def cmd_roommate(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.reply("Please register with /register first.")
        return

    lang_data = load_lang(user.language)
    await message.reply(lang_data.get("roommate_start", "Are you currently looking for a roommate? (yes/no)"))
    await state.set_state(RoommateStates.looking)

@router.message(RoommateStates.looking)
async def process_looking(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language)
    is_looking = message.text.lower()

    if is_looking not in [lang_data.get("yes", "yes"), lang_data.get("no", "no")]:
        await message.reply("Please answer with 'yes' or 'no'.")
        return

    user.roommate_prefs.looking_for_roommate = (is_looking == lang_data.get("yes", "yes"))

    if not user.roommate_prefs.looking_for_roommate:
        await save_user(user)
        await message.reply(lang_data.get("roommate_not_looking", "Your roommate search status has been updated."))
        await state.clear()
        return

    await message.reply(lang_data.get("roommate_ask_budget", "What is your monthly budget for rent? (e.g., 250-350)"))
    await state.set_state(RoommateStates.budget)

@router.message(RoommateStates.budget)
async def process_budget(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language)
    try:
        budget_min, budget_max = map(int, message.text.split('-'))
        await state.update_data(budget_min=budget_min, budget_max=budget_max)
    except ValueError:
        await message.reply("Please provide the budget as a range, e.g., '250-350'.")
        return

    await message.reply(lang_data.get("roommate_ask_smoker", "Do you smoke? (yes/no)"))
    await state.set_state(RoommateStates.smoker)

@router.message(RoommateStates.smoker)
async def process_smoker(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language)
    is_smoker = message.text.lower()
    if is_smoker not in [lang_data.get("yes", "yes"), lang_data.get("no", "no")]:
        await message.reply("Please answer with 'yes' or 'no'.")
        return
    await state.update_data(smoker=(is_smoker == lang_data.get("yes", "yes")))

    await message.reply(lang_data.get("roommate_ask_notes", "Any additional notes?"))
    await state.set_state(RoommateStates.notes)

@router.message(RoommateStates.notes)
async def process_notes(message: types.Message, state: FSMContext):
    form_data = await state.get_data()
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language)

    user.roommate_prefs.budget_min = form_data.get("budget_min")
    user.roommate_prefs.budget_max = form_data.get("budget_max")
    user.roommate_prefs.smoker = form_data.get("smoker")
    user.roommate_prefs.notes = message.text

    await save_user(user)
    await message.reply(lang_data.get("roommate_prefs_saved", "Your preferences have been saved!"))
    logger.info(f"User {message.from_user.id} updated roommate preferences.")
    await state.clear()

@router.message(Command("find_roommate"))
async def cmd_find_roommate(message: types.Message):
    user = await get_user(message.from_user.id)
    lang_data = load_lang(user.language if user else "en")
    if not user or not user.roommate_prefs.looking_for_roommate:
        await message.reply(lang_data.get("profile_not_found", "Please set your preferences using /roommate first."))
        return

    logger.info(f"User {user.user_id} is searching for roommates.")
    matches = await find_matching_roommates(user)

    if not matches:
        await message.reply(lang_data.get("roommate_no_matches", "No matching roommates found."))
        return

    await message.reply(lang_data.get("roommate_results_title", "Found {count} potential roommate(s):").format(count=len(matches)))
    for match in matches:
        response = (
            f"**Potential Roommate:**\n"
            f"- **Age:** {match.age or 'N/A'}\n"
            f"- **Smoker:** {'Yes' if match.roommate_prefs.smoker else 'No'}\n"
            f"- **Budget:** {match.roommate_prefs.budget_min}-{match.roommate_prefs.budget_max} EUR\n"
            f"- **Notes:** {match.roommate_prefs.notes or 'N/A'}"
        )
        await message.answer(response, parse_mode="Markdown")
