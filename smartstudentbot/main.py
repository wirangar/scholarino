import uvicorn
import os
import sys
from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, os.path.dirname(project_root))

from aiogram import Bot, Dispatcher, types
from smartstudentbot.config import TELEGRAM_BOT_TOKEN, BASE_URL, WEBHOOK_SECRET, BOT_ID, PORT
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.db_utils import init_db, SessionLocal
from smartstudentbot.handlers import (
    cmd_start, news_handler, register_handler, profile_handler, isee_handler,
    voice_handler, consult_handler, gamification_handler, cost_handler,
    live_chat_handler, admin_handler, ai_handler
)
from smartstudentbot.admin_web import routes as admin_routes

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

bot = Bot(token=TELEGRAM_BOT_TOKEN or "123:placeholder")
dp = Dispatcher()
app = FastAPI()

# Include bot handlers
# ... (all dp.include_router calls remain the same)
dp.include_router(cmd_start.router)
dp.include_router(news_handler.router)
dp.include_router(register_handler.router)
dp.include_router(profile_handler.router)
dp.include_router(isee_handler.router)
dp.include_router(voice_handler.router)
dp.include_router(consult_handler.router)
dp.include_router(gamification_handler.router)
dp.include_router(cost_handler.router)
dp.include_router(live_chat_handler.router)
dp.include_router(admin_handler.router)
dp.include_router(ai_handler.router)


# Mount admin web app
app.mount("/admin", admin_routes.router)

WEBHOOK_PATH = f"/{BOT_ID}/{WEBHOOK_SECRET}"

@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request, db: Session = Depends(get_db)):
    telegram_update = await request.json()
    update = types.Update(**telegram_update)
    # Pass the db session to the dispatcher if needed, or handle it in handlers
    await dp.feed_update(bot=bot, update=update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    init_db()
    # ... (rest of startup logic)
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "123:placeholder":
        logger.critical("TELEGRAM_BOT_TOKEN is not set! The bot cannot start.")
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
    logger.info("Shutting down bot session...")
    await bot.session.close()

@app.get("/")
async def root():
    return {"status": "alive", "bot_id": BOT_ID}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
