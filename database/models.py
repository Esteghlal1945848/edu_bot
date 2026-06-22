from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, JSON, Index
from datetime import datetime
from database.core import Base


class User(Base):
    __tablename__ = "users"
    id          = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username    = Column(String, nullable=True)
    full_name   = Column(String)


class Publisher(Base):
    __tablename__ = "publishers"
    id               = Column(Integer, primary_key=True)
    name             = Column(String, unique=True, index=True)
    type             = Column(String)          # institute | book_publisher
    subjects_by_major = Column(JSON, nullable=True)  # {"ریاضی": ["فیزیک", ...], "تجربی": [...]}
    created_at       = Column(DateTime, default=datetime.now)


class Teacher(Base):
    __tablename__ = "teachers"
    id           = Column(Integer, primary_key=True)
    name         = Column(String)
    publisher_id = Column(Integer, ForeignKey("publishers.id"), index=True)
    grade        = Column(String)
    major        = Column(String)
    subject      = Column(String)
    created_at   = Column(DateTime, default=datetime.now)

    __table_args__ = (
        # جستجوی دبیر بر اساس publisher + grade + major + subject خیلی رایجه
        Index("ix_teacher_lookup", "publisher_id", "grade", "major", "subject"),
    )


class Archive(Base):
    __tablename__ = "archives"
    id          = Column(Integer, primary_key=True)
    category    = Column(String, default="pdf")   # pdf | video | book
    type        = Column(String)                  # pdf | video
    grade       = Column(String)
    major       = Column(String)
    institute   = Column(String)                  # نام موسسه یا ناشر
    subject     = Column(String)
    teacher     = Column(String, nullable=True)
    book_name   = Column(String, nullable=True)
    file_id     = Column(String)
    file_name   = Column(String, nullable=True)
    caption     = Column(String, nullable=True)
    uploaded_by = Column(BigInteger)
    created_at  = Column(DateTime, default=datetime.now)

    __table_args__ = (
        # جستجوی آرشیو بر اساس category + grade + major + institute + subject
        Index("ix_archive_lookup", "category", "grade", "major", "institute", "subject"),
    )
