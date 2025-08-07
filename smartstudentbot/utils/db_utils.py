import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use absolute imports for robustness
from smartstudentbot.config import SQLITE_DB
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version
from smartstudentbot.models import User
from smartstudentbot.models_db import Base, News, UserDB

# Set up the database engine
# Using check_same_thread=False for SQLite is recommended for FastAPI/async apps
engine = create_engine(
    f"sqlite:///{SQLITE_DB}",
    connect_args={"check_same_thread": False} if "sqlite" in SQLITE_DB else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")

async def save_news(news: dict):
    """Saves a news item to the database and a backup JSON file."""
    session = SessionLocal()
    try:
        news_entry = News(
            title=news["title"],
            content=news["content"],
            file=news.get("file"),
            timestamp=news["timestamp"]
        )
        session.add(news_entry)
        session.commit()
        logger.info(f"News saved to DB: {news['title']}")

        json_path = "smartstudentbot/news.json"
        data = check_json_version(json_path)
        if data:
            data["data"].append(news)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save news: {e}")
        session.rollback()
    finally:
        session.close()

async def save_user(user: User):
    """Saves or updates a user's profile in the database."""
    session = SessionLocal()
    try:
        existing_user = session.query(UserDB).filter(UserDB.user_id == user.user_id).first()
        if existing_user:
            # Update existing user
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
            existing_user.age = user.age
            existing_user.country = user.country
            existing_user.field_of_study = user.field_of_study
            existing_user.email = user.email
            existing_user.language = user.language
            existing_user.preferences = json.dumps(user.preferences or {})
            logger.info(f"User {user.user_id} updated.")
        else:
            # Create new user
            new_user = UserDB(
                user_id=user.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                age=user.age,
                country=user.country,
                field_of_study=user.field_of_study,
                email=user.email,
                language=user.language,
                preferences=json.dumps(user.preferences or {})
            )
            session.add(new_user)
            logger.info(f"User {user.user_id} created.")
        session.commit()
    except Exception as e:
        logger.error(f"Failed to save user {user.user_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def get_user(user_id: int) -> User | None:
    """Retrieves a user's profile from the database."""
    session = SessionLocal()
    try:
        user_db = session.query(UserDB).filter(UserDB.user_id == user_id).first()
        if user_db:
            return User(
                user_id=user_db.user_id,
                first_name=user_db.first_name,
                last_name=user_db.last_name,
                age=user_db.age,
                country=user_db.country,
                field_of_study=user_db.field_of_study,
                email=user_db.email,
                language=user_db.language,
                preferences=json.loads(user_db.preferences or "{}")
            )
        return None
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None
    finally:
        session.close()
