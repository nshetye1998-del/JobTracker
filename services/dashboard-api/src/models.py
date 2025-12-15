from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=False)  # 'google' or 'microsoft'
    oauth_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to applications
    applications = relationship("Application", back_populates="user")

class CareerEvent(Base):
    __tablename__ = "career_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True) # Original email ID or unique event ID
    event_type = Column(String, index=True) # INTERVIEW, OFFER, REJECTION, OTHER
    company = Column(String, index=True)
    confidence = Column(Float)
    summary = Column(Text)
    raw_data = Column(JSON) # Store full event payload
    research_briefing = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
