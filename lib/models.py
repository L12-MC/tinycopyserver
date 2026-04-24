from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, LargeBinary, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ContentFile(Base):
    __tablename__ = "content_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    original_filename = Column(String)
    file_hash = Column(String, unique=True, index=True)
    size = Column(Integer)
    compressed_size = Column(Integer)
    content_type = Column(String)
    description = Column(Text)
    tags = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_torrent = Column(Boolean, default=False)
    torrent_data = Column(LargeBinary, nullable=True)
    downloads = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    uploaded_by = Column(String, default="anonymous")
    storage_path = Column(String)

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchIndex(Base):
    __tablename__ = "search_index"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, index=True)
    search_text = Column(String, index=True)
    keyword_weight = Column(Float)

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    total_uploaded = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
