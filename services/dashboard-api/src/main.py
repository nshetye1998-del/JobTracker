from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db, engine
from libs.core.db import Base, Application, User, ResearchCache
from src.auth import get_current_user, require_auth
from src.consumer import run_background_consumer
from libs.core.logger import configure_logger

logger = configure_logger("dashboard_api")

# Create tables on startup (using shared Base)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerOps Dashboard API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start Kafka Consumer
@app.on_event("startup")
async def startup_event():
    run_background_consumer()

# Pydantic Models
class ApplicationResponse(BaseModel):
    id: str
    company: Optional[str]
    role: Optional[str]
    status: Optional[str]
    confidence: Optional[float]
    summary: Optional[str]
    research_briefing: Optional[Any]
    created_at: Optional[datetime]
    storage_path: Optional[str]

    class Config:
        orm_mode = True

class StatsResponse(BaseModel):
    total_events: int
    interviews: int
    offers: int
    rejections: int

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/applications", response_model=List[ApplicationResponse])
def get_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get applications - filtered by user if authenticated"""
    query = db.query(Application).order_by(Application.created_at.desc())
    
    # Filter by user if authenticated
    if current_user:
        query = query.filter(Application.user_id == current_user.id)
    
    apps = query.offset(skip).limit(limit).all()
    return apps

@app.get("/applications/{event_id}", response_model=ApplicationResponse)
def get_application_by_id(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get single application by ID - with user access check"""
    query = db.query(Application).filter(Application.id == event_id)
    
    # Filter by user if authenticated
    if current_user:
        query = query.filter(Application.user_id == current_user.id)
    
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Event not found")
    return app

# Keep /events for backward compatibility if UI uses it, but map to Application
@app.get("/events", response_model=List[ApplicationResponse])
def get_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    return get_applications(skip, limit, db, current_user)

@app.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get stats - filtered by user if authenticated"""
    query = db.query(Application)
    
    # Filter by user if authenticated
    if current_user:
        query = query.filter(Application.user_id == current_user.id)
    
    total = query.count()
    interviews = query.filter(Application.status == "INTERVIEW").count()
    offers = query.filter(Application.status == "OFFER").count()
    rejections = query.filter(Application.status == "REJECTION").count()
    
    return {
        "total_events": total,
        "interviews": interviews,
        "offers": offers,
        "rejections": rejections
    }

# Research endpoints
@app.get("/research")
def get_research(
    company: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get research data from research_cache table"""
    query = db.query(ResearchCache)
    
    if company:
        query = query.filter(ResearchCache.company.ilike(f"%{company}%"))
    
    research_items = query.order_by(ResearchCache.researched_at.desc()).offset(skip).limit(limit).all()
    
    # Transform to API format
    research_data = []
    for item in research_items:
        research_data.append({
            "company": item.company,
            "role": item.role,
            "description": item.description,
            "salary_range": item.salary_range,
            "industry": item.industry,
            "company_size": item.company_size,
            "research_quality": item.research_quality * 100 if item.research_quality else 75,
            "data_source": item.data_source,
            "created_at": item.researched_at.isoformat() if item.researched_at else None,
        })
    
    return research_data

# Provider/Analytics endpoints
@app.get("/providers")
def get_providers(db: Session = Depends(get_db)):
    """Get provider statistics from application metadata"""
    # Mock provider data based on events
    total = db.query(Application).count()
    
    providers = [
        {
            "provider_name": "Groq",
            "name": "Groq",
            "total_requests": total,
            "successful_requests": total - 2,
            "failed_requests": 2,
            "avg_response_time": 1250.5
        },
        {
            "provider_name": "Tavily",
            "name": "Tavily",
            "total_requests": 7,
            "successful_requests": 7,
            "failed_requests": 0,
            "avg_response_time": 2340.2
        },
        {
            "provider_name": "Google Search",
            "name": "Google Search",
            "total_requests": 3,
            "successful_requests": 2,
            "failed_requests": 1,
            "avg_response_time": 890.7
        }
    ]
    
    return providers

