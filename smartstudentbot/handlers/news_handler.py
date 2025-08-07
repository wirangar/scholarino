import os
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Absolute imports for robustness
from smartstudentbot.config import ADMIN_CHAT_IDS, CHANNEL_ID, FEATURE_FLAGS
from smartstudentbot.utils.db_utils import save_news
from smartstudentbot.utils.gdrive import upload_file
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version

router = Router()

class NewsStates(StatesGroup):
    """Defines the states for the news posting FSM."""
    title = State()
    content = State()

@router.message(Command("post_news"))
async def post_news(message: types.Message, state: FSMContext):
    """Starts the process for an admin to post a new article."""
    if not FEATURE_FLAGS.get("NEWS", True):
        await message.reply("This feature is currently disabled.")
        return
    # Ensure ADMIN_CHAT_IDS contains strings for comparison
    if str(message.from_user.id) not in ADMIN_CHAT_IDS:
        await message.reply("Only admins can post news.")
        return
    await message.reply("Please enter the title of the news:")
    await state.set_state(NewsStates.title)

@router.message(NewsStates.title)
async def process_news_title(message: types.Message, state: FSMContext):
    """Processes the news title and asks for content."""
    await state.update_data(title=message.text)
    await message.reply("Please send the news content (text, PDF, image, or video):")
    await state.set_state(NewsStates.content)

@router.message(NewsStates.content)
async def process_news_content(message: types.Message, state: FSMContext):
    """Processes the news content, saves it, and publishes it."""
    data = await state.get_data()
    news = {
        "title": data["title"],
        "content": message.text or message.caption or "",
        "file": None,
        "timestamp": str(datetime.now())
    }

    file_to_upload = message.document or (message.photo[-1] if message.photo else message.video)

    if file_to_upload:
        # Use /tmp for downloads as it's guaranteed to be writeable
        temp_dir = "/tmp"

        file_info = await message.bot.get_file(file_to_upload.file_id)
        # Use a unique name to avoid collisions
        destination_path = os.path.join(temp_dir, f"{file_info.file_unique_id}.tmp")

        await message.bot.download_file(file_info.file_path, destination=destination_path)
        logger.info(f"File downloaded to {destination_path}")

        # The placeholder function expects a path
        news["file"] = upload_file(destination_path)

    await save_news(news)

    # Try sending to channel if configured
    if CHANNEL_ID and CHANNEL_ID != "@YourChannel":
        try:
            # Use a more compatible version of Markdown
            text_to_send = f"**{news['title']}**\n\n{news['content']}"
            await message.bot.send_message(CHANNEL_ID, text_to_send, parse_mode="MarkdownV2")
            logger.info(f"News sent to channel {CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Failed to send news to channel {CHANNEL_ID}: {e}")

    logger.info(f"News posted by admin {message.from_user.id}: {news['title']}")
    await message.reply("News has been published successfully!")
    await state.clear()

@router.message(Command("news"))
async def show_news(message: types.Message):
    """Displays the latest news articles to the user."""
    news_json_path = "smartstudentbot/news.json"
    data = check_json_version(news_json_path)

    if not data or not data.get("data"):
        await message.reply("There are no news articles at the moment.")
        return

    response = "*Latest News:*\n\n"
    # Show the last 5 news items
    for news_item in reversed(data["data"][-5:]):
        # Escape characters for MarkdownV2
        title = news_item['title'].replace('.', '\\.').replace('-', '\\-')
        content = news_item['content'].replace('.', '\\.').replace('-', '\\-')
        response += f"*{title}*\n{content}\n"
        if news_item.get("file"):
            response += f"[Download File]({news_item['file']})\n"
        response += "--- \n"

    await message.reply(response, parse_mode="MarkdownV2")
    logger.info(f"User {message.from_user.id} viewed news")
