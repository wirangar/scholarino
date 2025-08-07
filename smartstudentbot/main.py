import uvicorn
import os
import sys
from fastapi import FastAPI, Request

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, os.path.dirname(project_root))

from aiogram import Bot, Dispatcher, types
from smartstudentbot.config import TELEGRAM_BOT_TOKEN, BASE_URL, WEBHOOK_SECRET, BOT_ID, PORT
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.db_utils import init_db
from smartstudentbot.handlers import cmd_start, news_handler, register_handler, profile_handler

# Instantiate the bot with a placeholder token if the real one isn't set.
# The actual validation will happen in the on_startup event.
# This allows the module to be imported for testing without a .env file.
bot = Bot(token=TELEGRAM_BOT_TOKEN or "123:placeholder")
dp = Dispatcher()
app = FastAPI()

# Include routers
dp.include_router(cmd_start.router)
dp.include_router(news_handler.router)
dp.include_router(register_handler.router)
dp.include_router(profile_handler.router)

WEBHOOK_PATH = f"/{BOT_ID}/{WEBHOOK_SECRET}"

@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Process webhook updates from Telegram."""
    telegram_update = await request.json()
    update = types.Update(**telegram_update)
    await dp.feed_update(bot=bot, update=update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    """Initialize DB, validate config, and set the webhook on startup."""
    init_db()

    # Validate essential configuration now
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "123:placeholder":
        logger.critical("TELEGRAM_BOT_TOKEN is not set! The bot cannot start.")
        # In a real server, this might trigger a more graceful shutdown
        # For this context, exiting is fine.
        sys.exit(1)
    if not BASE_URL or not WEBHOOK_SECRET:
        logger.critical("BASE_URL or WEBHOOK_SECRET is not set! Webhook cannot be set.")
        sys.exit(1)

    webhook_url = f"{BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
    try:
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set for bot {BOT_ID} at {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    """Gracefully shut down the bot session."""
    logger.info("Shutting down bot session...")
    await bot.session.close()

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"status": "alive", "bot_id": BOT_ID}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
