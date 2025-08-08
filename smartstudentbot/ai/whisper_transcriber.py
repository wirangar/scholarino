import whisper
from typing import Optional
from smartstudentbot.utils.logger import logger

# Load the model once when the module is imported.
# Using the 'tiny' model as it's lightweight and suitable for a 512MB RAM environment.
logger.info("Loading Whisper model (tiny)...")
try:
    model = whisper.load_model("tiny")
    logger.info("Whisper model loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load Whisper model: {e}")
    model = None

async def transcribe_audio(file_path: str) -> Optional[str]:
    """
    Transcribes an audio file to text using the Whisper model.

    Args:
        file_path: The path to the audio file.

    Returns:
        The transcribed text as a string, or None if transcription fails.
    """
    if not model:
        logger.error("Whisper model is not loaded, cannot transcribe audio.")
        return None

    try:
        logger.info(f"Transcribing audio file at: {file_path}")
        result = model.transcribe(file_path)
        transcribed_text = result.get("text")
        logger.info(f"Transcription successful. Text: '{transcribed_text[:50]}...'")
        return transcribed_text
    except Exception as e:
        logger.error(f"Failed to transcribe audio file at {file_path}: {e}")
        return None
