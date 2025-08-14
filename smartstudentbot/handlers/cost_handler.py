import json
from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command

from ..utils.localization import get_string

router = Router()

# A simple (and temporary) way to get the user's language.
def get_user_lang(message: types.Message):
    # This should be replaced with a real state management system
    return "en"

@router.message(Command("cost"))
async def cmd_cost(message: types.Message):
    """
    Handler for the /cost command.
    Displays a formatted summary of living costs in Perugia.
    """
    lang = get_user_lang(message)

    # Load the cost of living data
    cost_path = Path(__file__).parent.parent / "cost_of_living.json"
    with open(cost_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build the response message
    response_lines = [f"*{get_string(lang, 'cost_of_living_title')}*"]

    # Monthly Costs
    response_lines.append(f"\n*{get_string(lang, 'monthly_costs_header')}*")
    for key, item in data.get("monthly_costs", {}).items():
        name = item.get(f"name_{lang}", key)
        value = item.get("range", "-")
        response_lines.append(f"• {name}: {value}")

    # One-Time Costs
    response_lines.append(f"\n*{get_string(lang, 'one_time_costs_header')}*")
    for key, item in data.get("one_time_costs", {}).items():
        name = item.get(f"name_{lang}", key)
        value = item.get("range", "-")
        response_lines.append(f"• {name}: {value}")

    # Summary
    response_lines.append(f"\n*{get_string(lang, 'total_estimate_header')}*")
    response_lines.append(data.get("summary", {}).get(lang, ""))

    response_text = "\n".join(response_lines)

    await message.answer(text=response_text, parse_mode="Markdown")
