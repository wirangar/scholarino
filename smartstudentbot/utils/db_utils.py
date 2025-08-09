import json
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from typing import List

# Use absolute imports for robustness
from smartstudentbot.config import DATABASE_URL, SQLITE_DB
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version
from smartstudentbot.models import User
from smartstudentbot.models_db import Base, News, UserDB

# Set up the database engine
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
        news_entry = News(**news)
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
        user_data = user.model_dump()
        user_data['preferences'] = json.dumps(user_data.get('preferences', {}))
        user_data['badges'] = json.dumps(user_data.get('badges', []))
        user_data['roommate_prefs'] = json.dumps(user_data.get('roommate_prefs', {}))

        if existing_user:
            for key, value in user_data.items():
                setattr(existing_user, key, value)
            logger.info(f"User {user.user_id} updated.")
        else:
            new_user = UserDB(**user_data)
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
                preferences=json.loads(user_db.preferences or "{}"),
                points=user_db.points,
                badges=json.loads(user_db.badges or "[]"),
                roommate_prefs=json.loads(user_db.roommate_prefs or "{}")
            )
        return None
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None
    finally:
        session.close()

async def add_points_to_user(user_id: int, points_to_add: int):
    """Adds points to a user's score."""
    session = SessionLocal()
    try:
        user = session.query(UserDB).filter(UserDB.user_id == user_id).first()
        if user:
            user.points += points_to_add
            session.commit()
            logger.info(f"Added {points_to_add} points to user {user_id}. New total: {user.points}")
        else:
            logger.warning(f"Attempted to add points to non-existent user {user_id}.")
    except Exception as e:
        logger.error(f"Failed to add points to user {user_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def get_leaderboard(limit: int = 10) -> List[User]:
    """Retrieves the top users for the leaderboard."""
    session = SessionLocal()
    try:
        top_users_db = session.query(UserDB).order_by(desc(UserDB.points)).limit(limit).all()
        return [
            User(
                user_id=user_db.user_id,
                first_name=user_db.first_name,
                points=user_db.points
            ) for user_db in top_users_db
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve leaderboard: {e}")
        return []
    finally:
        session.close()
