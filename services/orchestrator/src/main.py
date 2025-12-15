import json
import time
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
from prometheus_client import Counter, Gauge, make_asgi_app
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
import threading
from queue import Queue

logger = configure_logger("orchestrator_service")

# Prometheus metrics
sse_connections = Gauge('orchestrator_sse_connections', 'Number of active SSE connections')
events_streamed = Counter('orchestrator_events_streamed_total', 'Total events streamed via SSE')
notifications_consumed = Counter('orchestrator_notifications_consumed_total', 'Total notifications consumed from Kafka')

class OrchestratorConfig(BaseConfig):
    SERVICE_NAME: str = "orchestrator"
    KAFKA_GROUP_ID: str = "orchestrator_group"

config = get_config(OrchestratorConfig)

app = FastAPI(title="Orchestrator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Global thread-safe queue for incoming Kafka events
incoming_queue = Queue(maxsize=100)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[asyncio.Queue] = []

    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_connections.append(queue)
        sse_connections.set(len(self.active_connections))
        return queue

    def disconnect(self, queue: asyncio.Queue):
        if queue in self.active_connections:
            self.active_connections.remove(queue)
            sse_connections.set(len(self.active_connections))

    async def broadcast(self, event: dict):
        for queue in self.active_connections:
            await queue.put(event)

manager = ConnectionManager()

async def event_broadcaster():
    """Background task to move events from thread-safe queue to async client queues"""
    logger.info("Starting event broadcaster task...")
    while True:
        # Non-blocking get from thread-safe queue
        try:
            # We use a small sleep to prevent busy waiting, but check frequently
            if not incoming_queue.empty():
                event = incoming_queue.get_nowait()
                await manager.broadcast(event)
                events_streamed.inc()
            else:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in event broadcaster: {e}")
            await asyncio.sleep(1)

from libs.core.db import DatabaseClient, Application
from kafka import KafkaProducer
import datetime

# ... (imports)

# Initialize Clients
try:
    db = DatabaseClient(config)
except Exception as e:
    logger.error(f"DB Init failed: {e}")
    db = None

producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    logger.error(f"Kafka Init failed: {e}")

# ... (ConnectionManager and event_broadcaster)

async def daily_stats_scheduler():
    """Background task to run daily stats job at 08:00 AM"""
    logger.info("Starting daily stats scheduler...")
    while True:
        now = datetime.datetime.now()
        # Run at 08:00 AM
        if now.hour == 8 and now.minute == 0:
            logger.info("Running daily stats job...")
            try:
                if db and producer:
                    session = db.Session()
                    try:
                        # Get yesterday's stats
                        yesterday = (now - datetime.timedelta(days=1)).date()
                        apps = session.query(Application).filter(Application.created_at >= yesterday).all()
                        
                        interviews = sum(1 for a in apps if a.status == 'INTERVIEW')
                        offers = sum(1 for a in apps if a.status == 'OFFER')
                        rejections = sum(1 for a in apps if a.status == 'REJECTION')
                        
                        summary_text = f"🌅 **Daily Summary** ({yesterday}):\n• {len(apps)} new events\n• {interviews} interviews\n• {offers} offers\n• {rejections} rejections"
                        
                        # Publish notification
                        event = {
                            "event_id": f"daily_stats_{int(time.time())}",
                            "event_type": "DAILY_STATS",
                            "company": "System",
                            "role": "Daily Report",
                            "summary": summary_text,
                            "classified_at": now.isoformat(),
                            "metadata": {"type": "daily_stats"}
                        }
                        producer.send('notifications', event)
                        logger.info("Published daily stats notification")
                    finally:
                        session.close()
            except Exception as e:
                logger.error(f"Daily stats job failed: {e}")
            
            # Sleep for 61 seconds to avoid double run
            await asyncio.sleep(61)
        else:
            # Check every minute
            await asyncio.sleep(60)

def kafka_consumer_thread():
    """Background thread to consume from classified_events topic and save to database"""
    logger.info("Starting Kafka consumer thread for classified_events...")
    
    consumer = KafkaConsumer(
        'classified_events',
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        group_id=config.KAFKA_GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    
    logger.info("✅ Kafka consumer connected to 'classified_events' topic")
    
    for message in consumer:
        try:
            event = message.value
            notifications_consumed.inc()
            
            # Save to database
            if db:
                session = db.Session()
                try:
                    event_id = event.get('event_id', event.get('message_id'))
                    
                    # Check if application already exists (deduplication)
                    existing = session.query(Application).filter(Application.id == event_id).first()
                    
                    if existing:
                        # Update existing application
                        existing.company = event.get('company', existing.company)
                        existing.role = event.get('role', existing.role)
                        existing.status = event.get('event_type', existing.status)
                        existing.confidence = event.get('confidence', existing.confidence)
                        existing.summary = event.get('summary', existing.summary)
                        existing.research_briefing = event.get('research_briefing', existing.research_briefing)
                        existing.metadata_ = event.get('metadata', existing.metadata_)
                        existing.updated_at = datetime.datetime.utcnow()
                        session.commit()
                        logger.info(f"✅ Updated in DB: {event.get('event_type')} - {event.get('company')}")
                    else:
                        # Get default user (primary email account owner)
                        from libs.core.db import User
                        default_user = session.query(User).filter(User.email == 'nikunj.shetye@gmail.com').first()
                        
                        # Create new application
                        app = Application(
                            id=event_id,
                            company=event.get('company', 'Unknown'),
                            role=event.get('role', event.get('position', 'Unknown')),
                            status=event.get('event_type', 'OTHER'),
                            confidence=event.get('confidence', 0.0),
                            summary=event.get('summary', ''),
                            research_briefing=event.get('research_briefing'),
                            metadata_=event.get('metadata'),
                            user_id=default_user.id if default_user else None
                        )
                        session.add(app)
                        session.commit()
                        logger.info(f"✅ Saved to DB: {event.get('event_type')} - {event.get('company')} (user: {default_user.email if default_user else 'None'})")
                except Exception as e:
                    session.rollback()
                    logger.error(f"❌ Failed to save to DB: {e}")
                finally:
                    session.close()
            
            # Broadcast to SSE clients
            incoming_queue.put(event)
            
        except Exception as e:
            logger.error(f"Error processing notification: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Orchestrator Service...")
    asyncio.create_task(event_broadcaster())
    asyncio.create_task(daily_stats_scheduler())
    
    # Start Kafka consumer in background thread
    consumer_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    consumer_thread.start()
    logger.info("✅ Kafka consumer thread started")

# ... (kafka_consumer_thread)

@app.get("/events")
async def events(request: Request):
    """SSE endpoint for real-time updates to dashboard"""
    async def event_stream():
        queue = await manager.connect()
        try:
            # Send initial heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.datetime.utcnow().isoformat()})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("Client disconnected from SSE")
                    break
                
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat every 30 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.datetime.utcnow().isoformat()})}\n\n"
        finally:
            manager.disconnect(queue)
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/stats/today")
async def stats_today():
    """Get today's statistics"""
    if not db:
        return {"error": "Database not available"}
        
    session = db.Session()
    try:
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        apps = session.query(Application).filter(Application.created_at >= today_start).all()
        
        interviews = sum(1 for a in apps if a.status == 'INTERVIEW')
        offers = sum(1 for a in apps if a.status == 'OFFER')
        rejections = sum(1 for a in apps if a.status == 'REJECTION')
        
        return {
            "date": today_start.strftime("%Y-%m-%d"),
            "interviews": interviews,
            "offers": offers,
            "rejections": rejections,
            "total_events": len(apps)
        }
    finally:
        session.close()

@app.get("/stats/summary")
async def stats_summary():
    """Get overall summary statistics"""
    if not db:
        return {"error": "Database not available"}
        
    session = db.Session()
    try:
        total = session.query(Application).count()
        interviews = session.query(Application).filter(Application.status == 'INTERVIEW').count()
        offers = session.query(Application).filter(Application.status == 'OFFER').count()
        rejections = session.query(Application).filter(Application.status == 'REJECTION').count()
        
        return {
            "total_interviews": interviews,
            "total_offers": offers,
            "total_rejections": rejections,
            "active_applications": total - rejections
        }
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Orchestrator Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
