import json
import threading
import time
from kafka import KafkaConsumer
from sqlalchemy.orm import Session
from src.database import SessionLocal
from libs.core.db import Application, User  # Use shared models instead of local models
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("dashboard_consumer")

class ConsumerConfig(BaseConfig):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_GROUP_ID: str = "dashboard_group"

config = get_config(ConsumerConfig)

def process_message(db: Session, msg_value: dict):
    try:
        event_id = msg_value.get('event_id') or msg_value.get('id') or msg_value.get('original_email_id')
        if not event_id:
            logger.warning("Message missing ID, skipping.")
            return

        # Check if exists
        existing = db.query(Application).filter(Application.id == event_id).first()
        
        if existing:
            # Update
            existing.status = msg_value.get('event_type', existing.status)
            existing.company = msg_value.get('company', existing.company)
            existing.confidence = msg_value.get('confidence', existing.confidence)
            existing.summary = msg_value.get('summary', existing.summary)
            existing.metadata_ = msg_value  # Store full message in metadata
            if 'research_briefing' in msg_value:
                existing.research_briefing = msg_value['research_briefing']
            logger.info(f"Updated application {event_id}")
        else:
            # Resolve user_id from user_email if provided
            user_id = None
            user_email = msg_value.get("user_email")
            if user_email:
                user = db.query(User).filter_by(email=user_email).first()
                if user:
                    user_id = user.id
            
            # Create
            new_app = Application(
                id=event_id,
                company=msg_value.get('company'),
                role=msg_value.get('role'),
                status=msg_value.get('event_type'),
                confidence=msg_value.get('confidence'),
                summary=msg_value.get('summary'),
                metadata_=msg_value,
                research_briefing=msg_value.get('research_briefing'),
                storage_path=msg_value.get('storage_path'),
                user_id=user_id
            )
            db.add(new_app)
            logger.info(f"Created application {event_id}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        db.rollback()

def start_consumer():
    logger.info("Starting Dashboard Kafka Consumer...")
    
    # Retry connection
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'classified_events', 'notifications',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)
            
    db = SessionLocal()
    try:
        for message in consumer:
            logger.info(f"Received message from {message.topic}")
            process_message(db, message.value)
    except Exception as e:
        logger.error(f"Consumer crashed: {e}")
    finally:
        db.close()
        consumer.close()

def run_background_consumer():
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()
