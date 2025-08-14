from fastapi import FastAPI, Request, HTTPException, Response
from aiogram import Bot, Dispatcher
from aiogram.types import Update
import uvicorn
import os
import logging

# This will fail until config.py is in the python path, which it should be if running from the root dir.
from config import TELEGRAM_BOT_TOKEN, BASE_URL, WEBHOOK_SECRET, BOT_ID

# Use a basic logger for now
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the bot token is set
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

app = FastAPI()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# The prompt lists many handlers. We will add them here as they are created.
from .handlers import cmd_start, guide_handler, cost_handler, isee_handler
dp.include_router(cmd_start.router)
dp.include_router(guide_handler.router)
dp.include_router(cost_handler.router)
dp.include_router(isee_handler.router)

@app.post(f"/{WEBHOOK_SECRET}")
async def bot_webhook(request: Request):
    """
    This endpoint processes incoming updates from Telegram.
    """
    # The secret token is verified by Telegram by setting it in the webhook.
    # The header X-Telegram-Bot-Api-Secret-Token should be checked if you want extra security.
    # For now, relying on the secret URL is sufficient.

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=200)


@app.get("/health")
async def health_check():
    """
    A simple health check endpoint.
    """
    return {"status": "healthy"}


@app.on_event("startup")
async def on_startup():
    """
    Actions to perform on application startup.
    This is where we set the webhook.
    """
    webhook_url = f"{BASE_URL}/{WEBHOOK_SECRET}"
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.model_fields.keys(),  # Or specify a list like ["message", "callback_query"]
        secret_token=WEBHOOK_SECRET
    )
    logger.info(f"Webhook set to {webhook_url}")


@app.on_event("shutdown")
async def on_shutdown():
    """
    Actions to perform on application shutdown.
    This is where we delete the webhook.
    """
    logger.info("Shutting down webhook")
    await bot.delete_webhook()


# The original prompt had a typo in the name guard: `if name == "main":`
# This allows running the app directly with uvicorn for development.
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True  # Enable auto-reloading for development
    )
