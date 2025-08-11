from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from smartstudentbot.models import SuccessStory
from smartstudentbot.utils.db_utils import save_story, get_user, get_approved_stories
from smartstudentbot.utils.logger import logger

router = Router()

class SubmitStoryStates(StatesGroup):
    writing_story = State()

@router.message(Command("submit_story"))
async def cmd_submit_story(message: types.Message, state: FSMContext):
    """Starts the process for a user to submit their success story."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.reply("Please register with /register first.")
        return

    await message.reply("That's great! Please write down your success story and send it to me. Tell us about your journey, challenges, and achievements.")
    await state.set_state(SubmitStoryStates.writing_story)

@router.message(SubmitStoryStates.writing_story)
async def process_story_text(message: types.Message, state: FSMContext):
    """Receives the story text and saves it for moderation."""
    if not message.text or len(message.text) < 50:
        await message.reply("Your story seems a bit short. Please provide more details to inspire others!")
        return

    story = SuccessStory(
        user_id=message.from_user.id,
        story_text=message.text
    )

    await save_story(story)

    await message.reply("Thank you for sharing your story! It has been submitted for review and will be published after approval.")
    logger.info(f"User {message.from_user.id} submitted a success story.")
    await state.clear()

@router.message(Command("stories"))
async def cmd_stories(message: types.Message):
    """Displays approved success stories."""
    logger.info(f"User {message.from_user.id} requested to view success stories.")
    stories = await get_approved_stories()

    if not stories:
        await message.reply("No success stories have been published yet. Be the first to share yours with /submit_story!")
        return

    await message.reply("Here are some success stories from our community:")
    for story in stories[:5]: # Show latest 5 stories
        author = await get_user(story.user_id)
        author_name = author.first_name if author else "An anonymous user"
        response = (
            f"**Story from {author_name}**\n"
            f"-------------------------\n"
            f"_{story.story_text}_"
        )
        await message.answer(response, parse_mode="Markdown")
