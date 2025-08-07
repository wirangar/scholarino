import pytest
from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, User, Chat

from smartstudentbot.handlers.cmd_start import cmd_start_handler
from smartstudentbot.handlers.news_handler import show_news
from smartstudentbot.handlers.register_handler import cmd_register, RegisterStates
from smartstudentbot.handlers.profile_handler import cmd_profile
from smartstudentbot.utils.db_utils import save_user

@pytest.mark.asyncio
async def test_cmd_start(db_session):
    """
    Tests the /start command handler.
    """
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.from_user = User(id=123, is_bot=False, first_name="Test")
    message.chat = Chat(id=123, type="private")

    await cmd_start_handler(message)

    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    assert "Welcome to SmartStudentBot!" in args[0]

@pytest.mark.asyncio
async def test_show_news_no_news(db_session):
    """
    Tests the /news command when there are no news articles.
    """
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.from_user = User(id=123, is_bot=False, first_name="Test")

    await show_news(message)

    message.reply.assert_called_once_with("There are no news articles at the moment.")

@pytest.mark.asyncio
async def test_register_command_starts_fsm(db_session):
    """
    Tests that the /register command correctly starts the FSM.
    """
    # A token with a valid format is required for Bot initialization
    bot = Bot(token="123456:ABC-DEF")
    message = AsyncMock(spec=Message)
    message.from_user = User(id=123, is_bot=False, first_name="Test")
    message.chat = Chat(id=123, type="private")
    message.reply = AsyncMock()

    storage = MemoryStorage()
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=123)
    state = FSMContext(storage=storage, key=key)

    await cmd_register(message, state)

    message.reply.assert_called_once()
    assert await state.get_state() == RegisterStates.first_name

@pytest.mark.asyncio
async def test_profile_command_for_existing_user(db_session, sample_user):
    """
    Tests the /profile command for a user that exists in the database.
    """
    await save_user(sample_user)

    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.from_user = User(id=sample_user.user_id, is_bot=False, first_name="Test")

    await cmd_profile(message)

    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    reply_text = args[0]
    assert sample_user.first_name in reply_text
    assert sample_user.country in reply_text
    assert sample_user.email in reply_text

@pytest.mark.asyncio
async def test_profile_command_for_new_user(db_session):
    """
    Tests the /profile command for a user that does not exist.
    """
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.from_user = User(id=999, is_bot=False, first_name="New")

    await cmd_profile(message)

    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    assert "/register" in args[0]
