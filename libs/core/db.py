from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text, Float, pool, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from libs.core.config import BaseConfig
from libs.core.logger import configure_logger
import datetime

logger = configure_logger("db_client")
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=False)
    oauth_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    applications = relationship("Application", back_populates="user")

class Application(Base):
    __tablename__ = 'applications'

    id = Column(String, primary_key=True)  # event_id or message_id
    company = Column(String, index=True)
    role = Column(String)
    status = Column(String)  # INTERVIEW, OFFER, REJECTION, APPLIED
    confidence = Column(Float)
    summary = Column(Text)
    research_briefing = Column(JSON)
    metadata_ = Column("metadata", JSON)  # 'metadata' is reserved in SQLAlchemy sometimes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    storage_path = Column(String) # Link to MinIO
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # Nullable for existing events
    
    user = relationship("User", back_populates="applications")

class ResearchCache(Base):
    __tablename__ = 'research_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    description = Column(Text)
    salary_range = Column(String)
    industry = Column(String)
    company_size = Column(String)
    data_source = Column(String)
    research_quality = Column(Float)
    researched_at = Column(DateTime, default=datetime.datetime.utcnow)
    company_normalized = Column(String, index=True)
    role_normalized = Column(String, index=True)

class CompanyData(Base):
    __tablename__ = 'company_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    name_normalized = Column(String, index=True)  # Lowercase for matching
    domain = Column(String)
    year_founded = Column(Integer)
    industry = Column(String, index=True)
    size_range = Column(String)
    locality = Column(String)
    country = Column(String)
    linkedin_url = Column(String)
    current_employee_estimate = Column(Integer)
    total_employee_estimate = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DatabaseClient:
    def __init__(self, config: BaseConfig):
        # Create engine with connection pooling
        self.engine = create_engine(
            config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,              # Number of persistent connections
            max_overflow=20,           # Additional connections when pool is exhausted
            pool_timeout=30,           # Seconds to wait for connection
            pool_recycle=3600,         # Recycle connections after 1 hour
            pool_pre_ping=True,        # Test connections before use
            echo=False                 # Set to True for SQL debugging
        )
        
        # Use scoped_session for thread-safe session management
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        
        logger.info(f"✓ Database connection pool initialized (pool_size=10, max_overflow=20)")
        self._create_tables()

    def _create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created/verified.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def upsert_application(self, event: dict):
        with self.get_session() as session:
            # Resolve user_id from user_email if provided
            user_id = None
            user_email = event.get("user_email")
            if user_email:
                user = session.query(User).filter_by(email=user_email).first()
                if user:
                    user_id = user.id
                    logger.debug(f"Mapped user_email {user_email} to user_id {user_id}")
                else:
                    logger.warning(f"User not found for email {user_email}")
            
            # Map event to Application model
            app_data = {
                "id": event.get("event_id") or event.get("message_id"),
                "company": event.get("company"),
                "role": event.get("role"),
                "status": event.get("event_type"),
                "confidence": event.get("confidence"),
                "summary": event.get("summary"),
                "research_briefing": event.get("research_briefing"),
                "metadata_": event.get("metadata"),
                "storage_path": event.get("storage_path"),
                "user_id": user_id
            }

            # Check if exists
            existing = session.query(Application).filter_by(id=app_data["id"]).first()
            if existing:
                for key, value in app_data.items():
                    setattr(existing, key, value)
                logger.info(f"Updated application {app_data['id']}")
            else:
                new_app = Application(**app_data)
                session.add(new_app)
                logger.info(f"Created application {app_data['id']}")
    
    def save_research_cache(self, company: str, role: str, description: str, 
                           data_source: str = 'fallback', research_quality: float = 0.4,
                           salary_range: str = None, industry: str = None, company_size: str = None):
        """Save research data to research_cache table"""
        with self.get_session() as session:
            # Normalize for deduplication
            company_normalized = company.lower().strip()
            role_normalized = (role or 'general').lower().strip()
            
            # Check if exists (unique constraint on company_normalized + role_normalized)
            existing = session.query(ResearchCache).filter(
                func.lower(ResearchCache.company_normalized) == company_normalized,
                func.lower(ResearchCache.role_normalized) == role_normalized
            ).first()
            
            if existing:
                # Update existing research
                existing.description = description
                existing.data_source = data_source
                existing.research_quality = research_quality
                existing.salary_range = salary_range
                existing.industry = industry
                existing.company_size = company_size
                existing.researched_at = datetime.datetime.utcnow()
                logger.info(f"Updated research cache for {company} - {role}")
            else:
                # Create new research entry
                new_research = ResearchCache(
                    company=company,
                    role=role or 'General',
                    description=description,
                    salary_range=salary_range,
                    industry=industry,
                    company_size=company_size,
                    data_source=data_source,
                    research_quality=research_quality,
                    company_normalized=company_normalized,
                    role_normalized=role_normalized
                )
                session.add(new_research)
                logger.info(f"Created research cache for {company} - {role}")
    
    def get_company_data(self, company_name: str):
        """Retrieve company data from the company_data table"""
        with self.get_session() as session:
            company_normalized = company_name.lower().strip()
            
            # Try exact match first
            company = session.query(CompanyData).filter(
                CompanyData.name_normalized == company_normalized
            ).first()
            
            # If no exact match, try partial match
            if not company:
                company = session.query(CompanyData).filter(
                    CompanyData.name_normalized.like(f'%{company_normalized}%')
                ).first()
            
            if company:
                return {
                    'name': company.name,
                    'domain': company.domain,
                    'year_founded': company.year_founded,
                    'industry': company.industry,
                    'size_range': company.size_range,
                    'locality': company.locality,
                    'country': company.country,
                    'linkedin_url': company.linkedin_url,
                    'current_employees': company.current_employee_estimate,
                    'total_employees': company.total_employee_estimate
                }
            return None
    
    def get_pool_status(self):
        """Get connection pool statistics for monitoring"""
        return {
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow(),
            "total": self.engine.pool.size() + self.engine.pool.overflow()
        }
    
    def close(self):
        """Close all connections in the pool"""
        self.Session.remove()
        self.engine.dispose()
        logger.info("Database connection pool closed.")
