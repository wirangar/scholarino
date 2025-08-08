import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, User, Chat

from smartstudentbot.handlers.cmd_start import cmd_start_handler
from smartstudentbot.handlers.news_handler import show_news
from smartstudentbot.handlers.register_handler import cmd_register, RegisterStates
from smartstudentbot.handlers.profile_handler import cmd_profile
from smartstudentbot.handlers.isee_handler import cmd_isee, ISEEStates
from smartstudentbot.handlers import voice_handler
from smartstudentbot.handlers.consult_handler import cmd_consult, ConsultationStates
from smartstudentbot.handlers.gamification_handler import my_points_handler, leaderboard_handler
from smartstudentbot.utils.db_utils import save_user, add_points_to_user

@pytest.mark.asyncio
async def test_voice_message_handler(monkeypatch):
    """
    Tests the voice_handler by mocking the download, transcribe, and Q&A functions.
    """
    # 1. Mock the dependencies
    monkeypatch.setattr(voice_handler, "transcribe_audio", AsyncMock(return_value="What is a scholarship?"))
    monkeypatch.setattr(voice_handler, "get_answer", AsyncMock(return_value="A scholarship is a form of financial aid."))
    monkeypatch.setattr(voice_handler.os, "remove", MagicMock()) # Mock os.remove to avoid FileNotFoundError

    # 2. Mock the bot and message objects
    mock_bot = AsyncMock()
    mock_bot.get_file = AsyncMock(return_value=MagicMock(file_path="voice/file.oga"))
    mock_bot.download_file = AsyncMock()

    message = AsyncMock(spec=Message)
    message.bot = mock_bot
    message.voice = MagicMock()
    message.voice.file_id = "test_file_id"
    message.reply = AsyncMock()

    # 3. Call the handler
    await voice_handler.voice_message_handler(message)

    # 4. Assert the flow
    # It should download the file
    mock_bot.download_file.assert_called_once()
    # It should call the transcriber
    voice_handler.transcribe_audio.assert_called_once()
    # It should call the Q&A system
    voice_handler.get_answer.assert_called_once_with("What is a scholarship?")
    # It should reply with the final answer
    message.reply.assert_any_call("A scholarship is a form of financial aid.")


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

@pytest.mark.asyncio
async def test_isee_command_starts_fsm(db_session, sample_user):
    """
    Tests that the /isee command correctly starts the FSM for a registered user.
    """
    # 1. Save a user so they are considered "registered"
    await save_user(sample_user)

    # 2. Mock the message and FSM context
    bot = Bot(token="123456:ABC-DEF")
    message = AsyncMock(spec=Message)
    message.from_user = User(id=sample_user.user_id, is_bot=False, first_name="Test")
    message.reply = AsyncMock()

    storage = MemoryStorage()
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=sample_user.user_id)
    state = FSMContext(storage=storage, key=key)

    # 3. Call the handler
    await cmd_isee(message, state)

    # 4. Assert the bot replied and set the state
    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    assert "income" in args[0] # Check if it's asking for income
    assert await state.get_state() == ISEEStates.income

@pytest.mark.asyncio
async def test_consult_command_starts_fsm(db_session, sample_user):
    """
    Tests that the /consult command correctly starts the FSM for a registered user.
    """
    await save_user(sample_user)

    bot = Bot(token="123456:ABC-DEF")
    message = AsyncMock(spec=Message)
    message.from_user = User(id=sample_user.user_id, is_bot=False, first_name="Test")
    message.reply = AsyncMock()

    storage = MemoryStorage()
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=sample_user.user_id)
    state = FSMContext(storage=storage, key=key)

    await cmd_consult(message, state)

    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    assert "full name" in args[0].lower() # Check if it's asking for name
    assert await state.get_state() == ConsultationStates.name

@pytest.mark.asyncio
async def test_my_points_handler(db_session, sample_user):
    """
    Tests the /points command.
    """
    await save_user(sample_user)
    await add_points_to_user(sample_user.user_id, 77)

    message = AsyncMock(spec=Message)
    message.from_user = User(id=sample_user.user_id, is_bot=False, first_name="Test")
    message.reply = AsyncMock()

    await my_points_handler(message)

    message.reply.assert_called_once_with("You currently have 77 points.")

@pytest.mark.asyncio
async def test_leaderboard_handler(db_session, sample_user):
    """
    Tests the /leaderboard command.
    """
    await save_user(sample_user)
    await add_points_to_user(sample_user.user_id, 100)

    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()

    await leaderboard_handler(message)
    message.reply.assert_called_once()
    args, kwargs = message.reply.call_args
    assert "Top 10 Users" in args[0]
    assert "100 points" in args[0]
