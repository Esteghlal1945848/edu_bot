from sqlalchemy import (
    Column,
    Integer,
    String
)

from database.core import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    telegram_id = Column(Integer)

    username = Column(String)

    full_name = Column(String)


class File(Base):

    __tablename__ = "files"

    id = Column(
        Integer,
        primary_key=True
    )

    file_id = Column(String)

    file_type = Column(String)

    grade = Column(String)

    major = Column(String)

    subject = Column(String)
