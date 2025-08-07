from loguru import logger
import sys

# Ensure logs directory exists is handled by the initial setup
# In a real-world scenario, you might want to add a check here.
# os.makedirs("logs", exist_ok=True)

# Remove default handler
logger.remove()

# Add a handler to log to the console
logger.add(sys.stderr, level="INFO")

# Add a handler to log to a file
logger.add("smartstudentbot/logs/app.log", rotation="1 MB", level="DEBUG")

def log_action(action: str, user_id: int):
    logger.info(f"Action: {action}, User: {user_id}")
