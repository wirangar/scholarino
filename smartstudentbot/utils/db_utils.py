import json
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from typing import List

# Use absolute imports for robustness
from smartstudentbot.config import DATABASE_URL, SQLITE_DB
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.json_utils import read_json_file, write_json_file
from smartstudentbot.models import User, SuccessStory
from smartstudentbot.models_db import Base, News, UserDB, SuccessStoryDB

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
        data = read_json_file(json_path)
        if data:
            data["data"].append(news)
            write_json_file(json_path, data)
    except Exception as e:
        logger.error(f"Failed to save news: {e}")
        session.rollback()
    finally:
        session.close()

async def add_badge_to_user(user_id: int, badge_name: str):
    """Adds a new badge to a user if they don't have it already."""
    session = SessionLocal()
    try:
        user = session.query(UserDB).filter(UserDB.user_id == user_id).first()
        if user:
            badges = json.loads(user.badges or "[]")
            if badge_name not in badges:
                badges.append(badge_name)
                user.badges = json.dumps(badges)
                session.commit()
                logger.info(f"Added badge '{badge_name}' to user {user_id}.")
            else:
                logger.info(f"User {user_id} already has the badge '{badge_name}'.")
        else:
            logger.warning(f"Attempted to add badge to non-existent user {user_id}.")
    except Exception as e:
        logger.error(f"Failed to add badge to user {user_id}: {e}")
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

async def get_all_users() -> List[User]:
    """Retrieves all users from the database."""
    session = SessionLocal()
    try:
        users_db = session.query(UserDB).order_by(UserDB.user_id).all()
        return [
            User.model_validate(user_db, from_attributes=True) for user_db in users_db
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve all users: {e}")
        return []
    finally:
        session.close()

async def get_all_stories() -> List[SuccessStory]:
    """Retrieves all success stories, regardless of approval status."""
    session = SessionLocal()
    try:
        stories_db = session.query(SuccessStoryDB).order_by(desc(SuccessStoryDB.timestamp)).all()
        return [SuccessStory.model_validate(story, from_attributes=True) for story in stories_db]
    except Exception as e:
        logger.error(f"Failed to retrieve all stories: {e}")
        return []
    finally:
        session.close()

async def approve_story(story_id: int):
    """Approves a success story and awards points/badge to the author."""
    session = SessionLocal()
    try:
        story = session.query(SuccessStoryDB).filter(SuccessStoryDB.id == story_id).first()
        if story and not story.is_approved:
            story.is_approved = True
            session.commit() # Commit the approval first
            logger.info(f"Success story {story_id} approved.")

            # Now, award points and badge in a separate transaction
            # This makes the logic more robust.
            author_id = story.user_id
            await add_points_to_user(author_id, 50) # 50 points for an approved story
            await add_badge_to_user(author_id, "Inspirer")

    except Exception as e:
        logger.error(f"Failed to approve story {story_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def save_story(story: SuccessStory):
    """Saves a success story to the database."""
    session = SessionLocal()
    try:
        story_db = SuccessStoryDB(
            user_id=story.user_id,
            story_text=story.story_text,
            timestamp=str(story.timestamp),
            is_approved=story.is_approved
        )
        session.add(story_db)
        session.commit()
        logger.info(f"Success story from user {story.user_id} saved for moderation.")
    except Exception as e:
        logger.error(f"Failed to save success story for user {story.user_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def get_approved_stories() -> List[SuccessStory]:
    """Retrieves all approved success stories."""
    session = SessionLocal()
    try:
        stories_db = session.query(SuccessStoryDB).filter(SuccessStoryDB.is_approved == True).order_by(desc(SuccessStoryDB.timestamp)).all()
        return [SuccessStory.model_validate(story, from_attributes=True) for story in stories_db]
    except Exception as e:
        logger.error(f"Failed to retrieve approved stories: {e}")
        return []
    finally:
        session.close()

from smartstudentbot.models import GenderPreference

async def find_matching_roommates(user: User) -> List[User]:
    """Finds users with compatible roommate preferences using more advanced logic."""
    session = SessionLocal()
    try:
        if not user.roommate_prefs or not user.roommate_prefs.looking_for_roommate:
            return []

        # Get all potential candidates first
        candidates_db = session.query(UserDB).filter(
            UserDB.user_id != user.user_id,
            UserDB.roommate_prefs.contains('"looking_for_roommate": true')
        ).all()

        # Convert DB objects to Pydantic models for easier handling
        candidates = [
            User.model_validate(c, from_attributes=True) for c in candidates_db
        ]

        matches = []

        # Unpack user's preferences for easier access
        user_prefs = user.roommate_prefs
        user_gender = user.gender

        for candidate in candidates:
            candidate_prefs = candidate.roommate_prefs
            candidate_gender = candidate.gender

            # --- Two-way Gender Preference Check ---
            # My preference must match their gender
            my_pref_ok = (user_prefs.gender_preference == GenderPreference.ANY or
                          user_prefs.gender_preference.value == candidate_gender)
            # Their preference must match my gender
            their_pref_ok = (candidate_prefs.gender_preference == GenderPreference.ANY or
                             candidate_prefs.gender_preference.value == user_gender)

            if not (my_pref_ok and their_pref_ok):
                continue

            # --- Smoker Preference Check ---
            if user_prefs.smoker != candidate_prefs.smoker:
                continue

            # --- Budget Overlap Check ---
            my_min = user_prefs.budget_min or 0
            my_max = user_prefs.budget_max or float('inf')
            cand_min = candidate_prefs.budget_min or 0
            cand_max = candidate_prefs.budget_max or float('inf')

            if my_max < cand_min or cand_max < my_min:
                continue # No overlap

            # If all checks pass, it's a match
            matches.append(candidate)

        # Optional: Prioritize matches with the same field of study
        matches.sort(key=lambda m: m.field_of_study == user.field_of_study, reverse=True)

        return matches[:10] # Return top 10 matches

    except Exception as e:
        logger.error(f"Failed to find matching roommates for user {user.user_id}: {e}")
        return []
    finally:
        session.close()

async def get_news_by_id(news_id: int) -> News | None:
    """Retrieves a single news article by its ID."""
    session = SessionLocal()
    try:
        return session.query(News).filter(News.id == news_id).first()
    finally:
        session.close()

async def delete_news_by_id(news_id: int):
    """Deletes a news article by its ID."""
    session = SessionLocal()
    try:
        news_item = session.query(News).filter(News.id == news_id).first()
        if news_item:
            session.delete(news_item)
            session.commit()
            logger.info(f"News article {news_id} deleted.")
    except Exception as e:
        logger.error(f"Failed to delete news {news_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def update_news(news_id: int, title: str, content: str):
    """Updates a news article in the database."""
    session = SessionLocal()
    try:
        news_item = session.query(News).filter(News.id == news_id).first()
        if news_item:
            news_item.title = title
            news_item.content = content
            session.commit()
            logger.info(f"News article {news_id} updated.")
    except Exception as e:
        logger.error(f"Failed to update news {news_id}: {e}")
        session.rollback()
    finally:
        session.close()

async def get_all_news() -> List[News]:
    """Retrieves all news articles from the database."""
    session = SessionLocal()
    try:
        news_db = session.query(News).order_by(desc(News.timestamp)).all()
        return news_db
    except Exception as e:
        logger.error(f"Failed to retrieve all news: {e}")
        return []
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
