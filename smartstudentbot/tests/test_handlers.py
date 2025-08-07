import pytest
from unittest.mock import AsyncMock

from aiogram.types import Message, User, Chat
from smartstudentbot.handlers.cmd_start import cmd_start_handler

@pytest.mark.asyncio
async def test_cmd_start():
    """
    Tests the /start command handler.
    """
    # Mock the message object
    message = AsyncMock(spec=Message)

    # Explicitly make the 'reply' attribute an AsyncMock as well
    message.reply = AsyncMock()

    message.from_user = User(id=123, is_bot=False, first_name="Test")
    message.chat = Chat(id=123, type="private")

    # Call the handler
    await cmd_start_handler(message)

    # Assert that the reply method was called
    message.reply.assert_called_once()

    # You can also check the content of the reply
    args, kwargs = message.reply.call_args
    assert "Welcome to SmartStudentBot!" in args[0]

@pytest.mark.asyncio
async def test_show_news_no_news():
    """
    Tests the /news command when there are no news articles.
    """
    # Mock the message object
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.from_user = User(id=123, is_bot=False, first_name="Test")

    # Call the handler
    from smartstudentbot.handlers.news_handler import show_news
    await show_news(message)

    # Assert reply method was called with the correct message
    message.reply.assert_called_once_with("There are no news articles at the moment.")
