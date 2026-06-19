from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger
)

from database.core import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True
    )

    telegram_id = Column(
        BigInteger,
        unique=True
    )

    username = Column(
        String,
        nullable=True
    )

    full_name = Column(
        String
    )


class Archive(Base):

    __tablename__ = "archives"


    id = Column(
        Integer,
        primary_key=True
    )


    type = Column(
        String
    )
    # pdf
    # video


    grade = Column(
        String
    )


    major = Column(
        String
    )


    subject = Column(
        String
    )


    file_id = Column(
        String
    )


    caption = Column(
        String,
        nullable=True
    )


    uploaded_by = Column(
        BigInteger
    )
