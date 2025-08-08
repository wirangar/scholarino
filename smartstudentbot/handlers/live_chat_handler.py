from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from smartstudentbot.utils.logger import logger
from smartstudentbot.config import ADMIN_CHAT_IDS

router = Router()

# In-memory storage for active chats.
# In a production environment, this should be moved to Redis or a database.
# Structure: {user_id: admin_id, admin_id: user_id}
ACTIVE_CHATS = {}

class LiveChatStates(StatesGroup):
    in_chat = State()

@router.message(Command("live_chat"))
async def cmd_live_chat(message: types.Message, state: FSMContext, bot: Bot):
    """Initiates a live chat session request from a user."""
    user_id = message.from_user.id
    if user_id in ACTIVE_CHATS:
        await message.reply("You are already in a live chat session.")
        return

    logger.info(f"User {user_id} is requesting a live chat.")

    # Create an inline button for admins to accept the chat
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Accept Chat", callback_data=f"livechat_accept_{user_id}")]
    ])

    # Notify all admins
    for admin_id in ADMIN_CHAT_IDS:
        if not admin_id: continue
        try:
            await bot.send_message(
                admin_id,
                f"User {message.from_user.full_name} (@{message.from_user.username}, ID: {user_id}) is requesting a live chat.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send live chat request to admin {admin_id}: {e}")

    await state.set_state(LiveChatStates.in_chat)
    await message.reply("Connecting you to an admin... Please wait. Send your messages now.")

# This handler will catch any message from a user while they are in a live chat
@router.message(LiveChatStates.in_chat)
async def relay_user_to_admin(message: types.Message, bot: Bot):
    """Relays a message from a user to the connected admin."""
    user_id = message.from_user.id
    if user_id not in ACTIVE_CHATS:
        # Should not happen if state is set correctly, but as a safeguard
        await message.reply("You are not connected to an admin. Please start a new session with /live_chat.")
        return

    admin_id = ACTIVE_CHATS[user_id]

    try:
        # Forward the message to the admin to preserve original sender info
        await message.forward(chat_id=admin_id)
        logger.info(f"Relayed message from user {user_id} to admin {admin_id}")
    except Exception as e:
        logger.error(f"Failed to relay message from user {user_id} to admin {admin_id}: {e}")
        await message.reply("Sorry, there was an error sending your message to the admin.")


@router.message(Command("end_chat"))
async def cmd_end_chat(message: types.Message, state: FSMContext, bot: Bot):
    """Ends the current live chat session."""
    user_id = message.from_user.id

    if user_id not in ACTIVE_CHATS and str(user_id) not in ADMIN_CHAT_IDS:
        await message.reply("You are not in a live chat session.")
        return

    current_state = await state.get_state()
    if current_state != LiveChatStates.in_chat and str(user_id) not in ADMIN_CHAT_IDS:
        await message.reply("You are not in a live chat session.")
        return

    # Determine who is ending the chat and who to notify
    if user_id in ACTIVE_CHATS: # User is ending
        partner_id = ACTIVE_CHATS.pop(user_id)
        ACTIVE_CHATS.pop(partner_id, None)
        await bot.send_message(partner_id, "The user has ended the chat session.")
        await message.reply("You have ended the live chat.")
        await state.clear()
        logger.info(f"User {user_id} ended live chat with admin {partner_id}.")

    elif str(user_id) in ADMIN_CHAT_IDS: # Admin is ending
        admin_id = user_id
        if admin_id in ACTIVE_CHATS:
            partner_id = ACTIVE_CHATS.pop(admin_id)
            user_state = FSMContext(storage=state.storage, key=state.key.with_user_id(partner_id))
            await user_state.clear()
            ACTIVE_CHATS.pop(partner_id, None)
            await bot.send_message(partner_id, "The admin has ended the chat session.")
            await message.reply("You have ended the live chat.")
            logger.info(f"Admin {admin_id} ended live chat with user {partner_id}.")
        else:
            await message.reply("You are not currently in a chat with a user.")
    else:
        await message.reply("Could not end the chat. Are you in one?")
