from aiogram import Router, types, Bot
from aiogram.filters import Command
from .live_chat_handler import ACTIVE_CHATS
from ..utils.logger import logger

router = Router()

# This handler will catch any message from an admin that is a reply
# and check if they are in a live chat session.
@router.message(lambda message: message.from_user.id in ACTIVE_CHATS and message.reply_to_message)
async def relay_admin_to_user(message: types.Message, bot: Bot):
    """Relays a reply from an admin to the connected user."""
    admin_id = message.from_user.id
    user_id = ACTIVE_CHATS.get(admin_id)

    if not user_id:
        # Safeguard, should not happen if ACTIVE_CHATS is consistent
        return

    # Check if the admin is replying to a message forwarded from the user
    if message.reply_to_message.forward_from and message.reply_to_message.forward_from.id == user_id:
        try:
            # Send a copy of the admin's message to the user
            await bot.send_message(user_id, message.text)
            logger.info(f"Relayed message from admin {admin_id} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to relay message from admin {admin_id} to user {user_id}: {e}")
            await message.reply("Could not deliver your message to the user.")
    else:
        # The admin is replying to something else, not the user's message.
        # We can ignore this or add a hint.
        pass


@router.callback_query(lambda c: c.data and c.data.startswith('livechat_accept_'))
async def accept_live_chat(callback_query: types.CallbackQuery, bot: Bot):
    """Handles an admin accepting a live chat request."""
    admin_id = callback_query.from_user.id

    try:
        user_id = int(callback_query.data.split('_')[2])
    except (ValueError, IndexError):
        await callback_query.answer("Invalid callback data.", show_alert=True)
        return

    # Check if another admin has already accepted this chat
    if user_id in ACTIVE_CHATS:
        await callback_query.answer("This chat has already been accepted by another admin.", show_alert=True)
        # Prevent "Message is not modified" error by checking content
        if callback_query.message.text != f"Chat with user {user_id} was accepted by another admin.":
            await callback_query.message.edit_text(f"Chat with user {user_id} was accepted by another admin.")
        return

    # Check if the admin is already in another chat
    if admin_id in ACTIVE_CHATS:
        await callback_query.answer("You are already in another chat. Please end it first.", show_alert=True)
        return

    logger.info(f"Admin {admin_id} accepted live chat with user {user_id}.")

    # Establish the connection
    ACTIVE_CHATS[user_id] = admin_id
    ACTIVE_CHATS[admin_id] = user_id

    # Notify the user
    try:
        await bot.send_message(user_id, "An admin has connected. You can now chat live.")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id} about admin connection: {e}")
        # Rollback if we can't notify the user
        ACTIVE_CHATS.pop(user_id, None)
        ACTIVE_CHATS.pop(admin_id, None)
        await callback_query.answer("Could not notify the user. Please try again.", show_alert=True)
        return

    # Update the original message to show the chat was accepted
    await callback_query.answer("You have accepted the chat.")
    await callback_query.message.edit_text(f"You are now connected with user {user_id}.")
