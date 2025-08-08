from aiogram import Router, types
from aiogram.filters import Command

from smartstudentbot.utils.db_utils import get_leaderboard, get_user
from smartstudentbot.utils.logger import logger

router = Router()

@router.message(Command("points"))
async def my_points_handler(message: types.Message):
    """Displays the user's own points."""
    user = await get_user(message.from_user.id)
    if user:
        await message.reply(f"You currently have {user.points} points.")
    else:
        await message.reply("You need to register with /register first to see your points.")

@router.message(Command("leaderboard"))
async def leaderboard_handler(message: types.Message):
    """Displays the top 10 users by points."""
    logger.info("Fetching leaderboard.")
    top_users = await get_leaderboard(limit=10)

    if not top_users:
        await message.reply("The leaderboard is empty right now.")
        return

    response = "🏆 **Top 10 Users** 🏆\n\n"
    for i, user in enumerate(top_users, 1):
        # We need to escape MarkdownV2 special characters
        user_name = user.first_name.replace("-", "\\-").replace(".", "\\.")
        response += f"*{i}\\.* {user_name} \\- *{user.points} points*\n"

    await message.reply(response, parse_mode="MarkdownV2")
