from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/brew.db"

os.makedirs(os.path.dirname("./data/"), exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_database():
    inspector = inspect(engine)
    
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
        return
    
    columns = [col["name"] for col in inspector.get_columns("users")]
    
    with engine.connect() as conn:
        if "experience_points" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN experience_points INTEGER DEFAULT 0"))
            conn.commit()
        
        if "member_level" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN member_level VARCHAR DEFAULT 'apprentice'"))
            conn.commit()
    
    if not inspector.has_table("experience_records"):
        from app.models.models import ExperienceRecord
        ExperienceRecord.__table__.create(bind=engine)
    
    Base.metadata.create_all(bind=engine)
