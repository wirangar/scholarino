import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, User, Chat

# Import all handlers to be tested
from smartstudentbot.handlers import (
    cmd_start, news_handler, register_handler, profile_handler,
    isee_handler, voice_handler, consult_handler, gamification_handler,
    cost_handler, live_chat_handler, admin_handler
)
from smartstudentbot.utils.db_utils import save_user, add_points_to_user

# Helper function to create a standard mock message
def create_mock_message(user_id=123, bot_instance=None) -> AsyncMock:
    message = AsyncMock(spec=Message)
    message.from_user = User(id=user_id, is_bot=False, first_name="Test")
    message.chat = Chat(id=123, type="private")
    message.reply = AsyncMock()
    if bot_instance:
        message.bot = bot_instance
    return message

# Test for cmd_start
@pytest.mark.asyncio
async def test_cmd_start(db_session):
    message = create_mock_message()
    await cmd_start.cmd_start_handler(message)
    message.reply.assert_called_once()
    assert "Welcome" in message.reply.call_args[0][0]

# Test for news_handler
@pytest.mark.asyncio
async def test_show_news_no_news(db_session):
    message = create_mock_message()
    await news_handler.show_news(message)
    message.reply.assert_called_once_with("There are no news articles at the moment.")

# Test for register_handler
@pytest.mark.asyncio
async def test_register_command_starts_fsm(db_session):
    bot = Bot(token="123456:ABC-DEF")
    message = create_mock_message()
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=123)
    state = FSMContext(storage=MemoryStorage(), key=key)
    await register_handler.cmd_register(message, state)
    assert await state.get_state() == register_handler.RegisterStates.first_name

# Test for profile_handler
@pytest.mark.asyncio
async def test_profile_command_for_existing_user(db_session, sample_user):
    await save_user(sample_user)
    message = create_mock_message(user_id=sample_user.user_id)
    await profile_handler.cmd_profile(message)
    message.reply.assert_called_once()
    assert "Your Profile" in message.reply.call_args[0][0]

# Test for isee_handler
@pytest.mark.asyncio
async def test_isee_command_starts_fsm(db_session, sample_user):
    await save_user(sample_user)
    bot = Bot(token="123456:ABC-DEF")
    message = create_mock_message(user_id=sample_user.user_id)
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=sample_user.user_id)
    state = FSMContext(storage=MemoryStorage(), key=key)
    await isee_handler.cmd_isee(message, state)
    assert await state.get_state() == isee_handler.ISEEStates.income

# Test for voice_handler
@pytest.mark.asyncio
async def test_voice_message_handler(monkeypatch):
    monkeypatch.setattr(voice_handler, "transcribe_audio", AsyncMock(return_value="What is a scholarship?"))
    monkeypatch.setattr(voice_handler, "get_answer", AsyncMock(return_value="A scholarship is a form of financial aid."))
    monkeypatch.setattr(voice_handler.os, "remove", MagicMock())
    mock_bot = AsyncMock()
    mock_bot.get_file = AsyncMock(return_value=MagicMock(file_path="voice/file.oga", file_unique_id="unique_id"))
    message = create_mock_message(bot_instance=mock_bot)
    message.voice = MagicMock(file_id="test_file_id")
    await voice_handler.voice_message_handler(message)
    voice_handler.get_answer.assert_called_once_with("What is a scholarship?")

# Test for consult_handler
@pytest.mark.asyncio
async def test_consult_command_starts_fsm(db_session, sample_user):
    await save_user(sample_user)
    bot = Bot(token="123456:ABC-DEF")
    message = create_mock_message(user_id=sample_user.user_id)
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=sample_user.user_id)
    state = FSMContext(storage=MemoryStorage(), key=key)
    await consult_handler.cmd_consult(message, state)
    assert await state.get_state() == consult_handler.ConsultationStates.name

# Tests for gamification_handler
@pytest.mark.asyncio
async def test_my_points_handler(db_session, sample_user):
    await save_user(sample_user)
    await add_points_to_user(sample_user.user_id, 77)
    message = create_mock_message(user_id=sample_user.user_id)
    await gamification_handler.my_points_handler(message)
    message.reply.assert_called_once_with("You currently have 77 points.")

@pytest.mark.asyncio
async def test_leaderboard_handler(db_session, sample_user):
    await save_user(sample_user)
    message = create_mock_message()
    await gamification_handler.leaderboard_handler(message)
    message.reply.assert_called_once()

# Test for cost_handler
@pytest.mark.asyncio
async def test_cost_of_living_handler(db_session):
    message = create_mock_message()
    await cost_handler.cost_of_living_handler(message)
    message.reply.assert_called_once()

# Tests for live_chat_handler and admin_handler
@pytest.mark.asyncio
async def test_live_chat_command_starts_session(db_session, monkeypatch):
    monkeypatch.setattr(live_chat_handler, "ADMIN_CHAT_IDS", ["98765"])
    bot = Bot(token="123456:ABC-DEF")
    bot.send_message = AsyncMock()
    message = create_mock_message(bot_instance=bot)
    key = StorageKey(bot_id=bot.id, chat_id=123, user_id=123)
    state = FSMContext(storage=MemoryStorage(), key=key)
    await live_chat_handler.cmd_live_chat(message, state, bot)
    bot.send_message.assert_called()
    assert await state.get_state() == live_chat_handler.LiveChatStates.in_chat

@pytest.mark.asyncio
async def test_admin_accept_live_chat(db_session):
    bot = Bot(token="123456:ABC-DEF")
    bot.send_message = AsyncMock()
    callback_query = AsyncMock(spec=types.CallbackQuery)
    callback_query.from_user = User(id=987, is_bot=False, first_name="Admin")
    callback_query.data = "livechat_accept_123"
    callback_query.message = create_mock_message()
    callback_query.message.edit_text = AsyncMock()
    callback_query.answer = AsyncMock()
    live_chat_handler.ACTIVE_CHATS.clear()
    await admin_handler.accept_live_chat(callback_query, bot)
    assert live_chat_handler.ACTIVE_CHATS.get(123) == 987
    bot.send_message.assert_called_once_with(123, "An admin has connected. You can now chat live.")
