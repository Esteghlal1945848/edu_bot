from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, JSON
from datetime import datetime
from database.core import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String, nullable=True)
    full_name = Column(String)

class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)  # institute, book_publisher
    subjects_by_grade = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    publisher_id = Column(Integer, ForeignKey("publishers.id"))
    grade = Column(String)
    major = Column(String)
    subject = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Archive(Base):
    __tablename__ = "archives"
    id = Column(Integer, primary_key=True)
    category = Column(String, default="pdf")
    type = Column(String)
    grade = Column(String)
    major = Column(String)
    institute = Column(String)
    subject = Column(String)
    teacher = Column(String, nullable=True)
    book_name = Column(String, nullable=True)
    file_id = Column(String)
    file_name = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    uploaded_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    session_number = Column(Integer)
    title = Column(String, nullable=True)
    file_id = Column(String)
    file_name = Column(String)
    caption = Column(String, nullable=True)
    uploaded_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now)
