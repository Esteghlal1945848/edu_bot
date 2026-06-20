# ============================================
# database/models.py
# ============================================
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from datetime import datetime
from database.core import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String, nullable=True)
    full_name = Column(String)

class Archive(Base):
    __tablename__ = "archives"
    id = Column(Integer, primary_key=True)
    category = Column(String, default="pdf")  # pdf, video, book
    type = Column(String)  # pdf, video
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
