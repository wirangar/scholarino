import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# Use absolute imports for robustness
from smartstudentbot.config import SQLITE_DB
from smartstudentbot.utils.logger import logger
from smartstudentbot.utils.common import check_json_version

# Define the base for SQLAlchemy models
Base = declarative_base()

class News(Base):
    """SQLAlchemy model for news articles."""
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    file = Column(String, nullable=True)
    timestamp = Column(String)

try:
    # Set up the database engine and create tables if they don't exist
    # The database file will be in the root directory
    engine = create_engine(f"sqlite:///{SQLITE_DB}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
except Exception as e:
    logger.critical(f"Failed to initialize database: {e}")
    Session = None

async def save_news(news: dict):
    """
    Saves a news item to the SQLite database and the backup JSON file.
    """
    if Session is None:
        logger.error("Database session is not available. Cannot save news.")
        return

    session = Session()
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

        # Also save to news.json for compatibility/backup as requested
        # Note: In a real app, this dual-write might be handled by a more robust system
        json_path = "smartstudentbot/news.json"
        data = check_json_version(json_path)
        if data:
            data["data"].append(news)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"News also saved to {json_path}")

    except Exception as e:
        logger.error(f"Failed to save news: {e}")
        session.rollback()
    finally:
        session.close()
