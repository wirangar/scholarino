import pytest
from unittest.mock import AsyncMock

# Since our handlers are in a sibling directory, we need to adjust the path
# for pytest to find them. A better solution would be to install the project
# in editable mode, but for now, this works.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from handlers import cmd_start, guide_handler
from utils.localization import get_string


# A mock structure for a Telegram message to be used in tests
class MockMessage(AsyncMock):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.answer = AsyncMock()

@pytest.mark.asyncio
async def test_cmd_start_handler():
    """
    Tests the /start command handler.
    It should reply with a welcome message and a keyboard with 3 language buttons.
    """
    message = MockMessage()
    await cmd_start.cmd_start(message)

    # Check that the answer method was called once
    message.answer.assert_called_once()

    # Get the arguments passed to the answer method
    args, kwargs = message.answer.call_args

    # Check the welcome text
    expected_text = get_string("en", "welcome")
    assert "text" in kwargs and kwargs["text"] == expected_text

    # Check that a reply markup was provided and it has a keyboard
    assert "reply_markup" in kwargs
    keyboard = kwargs["reply_markup"]
    assert keyboard is not None

    # Check that the keyboard has 3 buttons
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 3

    # Check the text of the buttons
    button_texts = [button.text for button in keyboard.inline_keyboard[0]]
    assert get_string("en", "lang_button_en") in button_texts
    assert get_string("en", "lang_button_fa") in button_texts
    assert get_string("en", "lang_button_it") in button_texts

@pytest.mark.asyncio
async def test_cmd_guide_handler():
    """
    Tests the /guide command handler.
    It should reply with the guide menu and a keyboard with 3 topic buttons.
    """
    message = MockMessage()
    await guide_handler.cmd_guide(message)

    # Check that the answer method was called once
    message.answer.assert_called_once()

    # Get the arguments
    args, kwargs = message.answer.call_args

    # Check the menu title text
    expected_text = get_string("en", "guide_menu_title")
    assert "text" in kwargs and kwargs["text"] == expected_text

    # Check the keyboard
    assert "reply_markup" in kwargs
    keyboard = kwargs["reply_markup"]
    assert keyboard is not None

    # Check that the keyboard has 3 buttons
    assert len(keyboard.inline_keyboard) > 0 # It will have 2 rows
    all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    assert len(all_buttons) == 3

    # Check the button texts
    button_texts = [button.text for button in all_buttons]
    assert get_string("en", "guide_button_housing") in button_texts
    assert get_string("en", "guide_button_transport") in button_texts
    assert get_string("en", "guide_button_university") in button_texts
