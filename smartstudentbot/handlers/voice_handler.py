import os
from aiogram import Router, types, F
from smartstudentbot.utils.logger import logger
from smartstudentbot.ai.whisper_transcriber import transcribe_audio
from smartstudentbot.ai.question_answering import get_answer

router = Router()

@router.message(F.voice)
async def voice_message_handler(message: types.Message):
    """
    Handles incoming voice messages, transcribes them, and processes the text.
    """
    temp_dir = "/tmp"

    # Download the voice message
    try:
        file_info = await message.bot.get_file(message.voice.file_id)
        # Use a unique name to avoid collisions
        destination_path = os.path.join(temp_dir, f"{file_info.file_unique_id}.oga")

        await message.bot.download_file(file_info.file_path, destination=destination_path)
        logger.info(f"Voice message downloaded to {destination_path}")
    except Exception as e:
        logger.error(f"Failed to download voice message: {e}")
        await message.reply("Sorry, I couldn't process your voice message at the moment.")
        return

    # Transcribe the audio file
    transcribed_text = await transcribe_audio(destination_path)

    # Clean up the downloaded file
    os.remove(destination_path)

    if not transcribed_text:
        logger.warning(f"Transcription failed for voice message from user {message.from_user.id}")
        await message.reply("I had trouble understanding your voice message. Could you please try again?")
        return

    await message.reply(f"I heard: \"{transcribed_text}\"")
    logger.info(f"Transcription result: '{transcribed_text}'")

    # (Next Step) Now, process the transcribed text with the Q&A system
    answer = await get_answer(transcribed_text)

    if answer:
        await message.reply(answer)
    else:
        await message.reply("I understood your question, but I don't have an answer for it right now.")
