from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Boolean
)

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(
        BigInteger,
        unique=True,
        index=True
    )

    username = Column(String(100))
    full_name = Column(String(200))

    is_admin = Column(Boolean, default=False)

    join_date = Column(
        DateTime,
        default=datetime.utcnow
    )

    search_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)

    name = Column(String(200))
    bio = Column(Text)

    photo = Column(String(500))

    subjects = Column(JSON)

    rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)

    courses_count = Column(Integer, default=0)

    joined_date = Column(
        DateTime,
        default=datetime.utcnow
    )


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True)

    title = Column(String(500))
    description = Column(Text)

    content_type = Column(String(20))

    file_id = Column(String(200))
    file_size = Column(Integer)

    duration = Column(Integer)

    grade = Column(String(20))
    lesson = Column(String(100))
    chapter = Column(String(200))

    tags = Column(JSON)

    rating = Column(Float, default=0.0)

    views = Column(Integer, default=0)
    downloads = Column(Integer, default=0)

    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id")
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    content_id = Column(
        Integer,
        ForeignKey("contents.id")
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    content_id = Column(
        Integer,
        ForeignKey("contents.id")
    )

    downloaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    query = Column(String(500))

    results_count = Column(Integer)

    searched_at = Column(
        DateTime,
        default=datetime.utcnow
    )