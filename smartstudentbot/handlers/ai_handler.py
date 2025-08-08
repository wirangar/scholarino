from aiogram import Router, types, F
from smartstudentbot.ai.question_answering import get_answer
from smartstudentbot.utils.logger import logger

router = Router()

@router.message(F.text & ~F.text.startswith('/'))
async def ai_answer_handler(message: types.Message):
    """
    Handles non-command text messages by passing them to the AI Q&A system.
    """
    logger.info(f"User {message.from_user.id} sent a text message for AI handler: '{message.text}'")

    answer = await get_answer(message.text)

    if answer:
        await message.reply(answer)
    else:
        # A default response if no answer is found.
        # This can be enhanced later to queue the question for an admin.
        await message.reply("I'm sorry, I don't have an answer for that right now. I am still learning!")
        logger.info(f"No answer found for question: '{message.text}'")
