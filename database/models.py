from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Boolean
)

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    telegram_id = Column(
        Integer,
        unique=True,
        index=True
    )

    username = Column(
        String(100)
    )

    full_name = Column(
        String(200)
    )


class Archive(Base):

    __tablename__ = "archives"

    id = Column(
        Integer,
        primary_key=True
    )

    grade = Column(
        String(50)
    )

    major = Column(
        String(50)
    )

    subject = Column(
        String(100)
    )

    title = Column(
        String(300)
    )

    description = Column(
        Text
    )

    file_id = Column(
        Text
    )

    file_type = Column(
        String(30)
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
