from aiogram import Router, types, F
from smartstudentbot.ai.question_answering import get_answer
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.db_utils import add_points_to_user

router = Router()

@router.message(F.text & ~F.text.startswith('/'))
async def ai_answer_handler(message: types.Message):
    """
    Handles non-command text messages by passing them to the AI Q&A system.
    Awards points for successful answers.
    """
    logger.info(f"User {message.from_user.id} sent a text message for AI handler: '{message.text}'")

    answer = await get_answer(message.text)

    if answer:
        await message.reply(answer)
        # Award points for getting a successful answer
        await add_points_to_user(message.from_user.id, 5)
    else:
        # A default response if no answer is found.
        # This can be enhanced later to queue the question for an admin.
        await message.reply("I'm sorry, I don't have an answer for that right now. I am still learning!")
        logger.info(f"No answer found for question: '{message.text}'")
