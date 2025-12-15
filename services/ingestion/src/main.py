import time
import json
import os
import psycopg2
from datetime import datetime
from typing import List, Dict, Optional, Set
from kafka import KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from src.gmail_client import GmailClient
from src.outlook_client import OutlookClient
from src.email_filter import EmailRelevanceFilter
from libs.core.validation import validate_raw_email, compute_dedupe_key_from_email
from prometheus_client import Counter, Gauge, start_http_server

logger = configure_logger("ingestion_service")

# Prometheus metrics
emails_processed = Counter('ingestion_emails_processed_total', 'Total emails processed', ['source'])
emails_duplicates = Counter('ingestion_emails_duplicates_total', 'Total duplicate emails skipped')
emails_filtered = Counter('ingestion_emails_filtered_total', 'Total spam/non-job emails filtered', ['reason'])
emails_validation_errors = Counter('ingestion_emails_validation_errors_total', 'Total validation errors')
emails_dlq = Counter('ingestion_emails_dlq_total', 'Total emails sent to DLQ')
emails_published = Counter('ingestion_emails_published_total', 'Total emails published to Kafka')
batch_size_gauge = Gauge('ingestion_batch_size', 'Current batch size')
batches_flushed = Counter('ingestion_batches_flushed_total', 'Total batches flushed')

class IngestionConfig(BaseConfig):
    SERVICE_NAME: str = "ingestion"
    POLL_INTERVAL_SECONDS: int = 60
    BATCH_SIZE: int = 15  # Reduced to respect Gemini API rate limits (15 RPM)
    BATCH_TIMEOUT_SECONDS: int = 30
    # Outlook configuration
    OUTLOOK_USER_EMAIL: Optional[str] = None  # User's Outlook email address

config = get_config(IngestionConfig)

from libs.core.storage import StorageClient

def connect_to_database():
    """Connect to production PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'job_tracker_prod'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
        )
        logger.info("✓ Connected to production database for deduplication")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def is_email_processed(db_conn, email_id: str) -> bool:
    """
    Check if email has already been processed
    
    This is the critical deduplication layer that prevents reprocessing
    the same emails on every restart.
    
    NOTE: Table 'processed_emails' may not exist in current schema.
    Gracefully returns False (treat as new email) when table is missing.
    """
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_emails WHERE email_id = %s LIMIT 1",
            (email_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except psycopg2.Error as e:
        # CRITICAL: Rollback the failed transaction to prevent cascade errors
        db_conn.rollback()
        # Only log the first error, not every subsequent check
        if "processed_emails" in str(e):
            # Table doesn't exist - this is expected, treat all emails as new
            return False
        logger.error(f"Error checking processed email: {e}")
        return False
    except Exception as e:
        db_conn.rollback()
        logger.error(f"Unexpected error checking processed email: {e}")
        return False

def mark_as_processed(db_conn, email_id: str, source: str, classification: str = 'PENDING'):
    """Mark email as processed in database"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO processed_emails (email_id, source, classification)
            VALUES (%s, %s, %s)
            ON CONFLICT (email_id) DO NOTHING
            """,
            (email_id, source, classification)
        )
        db_conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error marking email as processed: {e}")
        db_conn.rollback()

def extract_gmail_header(message: dict, header_name: str) -> str:
    """Extract a specific header from Gmail message payload"""
    if not message or 'payload' not in message:
        return ''
    
    headers = message.get('payload', {}).get('headers', [])
    for header in headers:
        if header.get('name', '').lower() == header_name.lower():
            return header.get('value', '')
    return ''

def main():
    logger.info("=" * 80)
    logger.info("🚀 Starting Intelligent Ingestion Service v2.0")
    logger.info("=" * 80)
    logger.info("Features:")
    logger.info("  ✓ Multi-source: Gmail + Outlook")
    logger.info("  ✓ Persistent deduplication (never reprocess emails)")
    logger.info("  ✓ Batched delivery (Kafka)")
    logger.info("=" * 80)
    logger.info(f"📦 Batch config: size={config.BATCH_SIZE}, timeout={config.BATCH_TIMEOUT_SECONDS}s")
    
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Prometheus metrics available at :8001/metrics")
    
    # Connect to production database for deduplication
    logger.info("Connecting to production database...")
    try:
        db_conn = connect_to_database()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return
    
    # Initialize Clients
    gmail = GmailClient()
    
    # Initialize email relevance filter
    email_filter = EmailRelevanceFilter()
    logger.info("✅ Email relevance filter initialized")
    
    # Only initialize Outlook if user authenticated (token cache exists)
    import os
    if os.path.exists('outlook_token_cache.json'):
        outlook = OutlookClient()
    else:
        outlook = None
        logger.info("⚠️ Outlook not configured. Run authenticate_outlook.py to enable.")
    
    storage = StorageClient(config)
    
    # Log which sources are enabled
    sources_enabled = []
    if gmail:
        sources_enabled.append("Gmail")
    if outlook and outlook.enabled:
        sources_enabled.append("Outlook")
        logger.info(f"📧 Outlook user email: {config.OUTLOOK_USER_EMAIL}")
    logger.info(f"✅ Email sources enabled: {', '.join(sources_enabled) if sources_enabled else 'None'}")
    
    # Batch processing state
    batch: List[Dict] = []
    last_flush_time = time.time()
    
    # Initialize Kafka Producer
    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka Producer connected.")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")

    def should_flush_batch() -> bool:
        """Decide if batch should be flushed now"""
        if not batch:
            return False
        
        # Reason 1: Batch is full
        if len(batch) >= config.BATCH_SIZE:
            logger.info(f"🔔 Batch size limit reached ({config.BATCH_SIZE})")
            return True
        
        # Reason 2: Timeout reached
        time_since_last_flush = time.time() - last_flush_time
        if time_since_last_flush >= config.BATCH_TIMEOUT_SECONDS:
            logger.info(f"⏰ Batch timeout reached ({config.BATCH_TIMEOUT_SECONDS}s with {len(batch)} emails)")
            return True
        
        return False

    def flush_batch():
        """Send batch to Kafka"""
        nonlocal batch, last_flush_time
        
        if not batch:
            logger.debug("No emails in batch, skipping flush")
            return
        
        try:
            batch_size = len(batch)
            logger.info(f"🚀 Flushing batch of {batch_size} emails...")
            
            # Send batch to Kafka (SINGLE message)
            batch_message = {
                'emails': batch,
                'count': len(batch),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if producer:
                producer.send('raw_inbox_batch', batch_message)
                producer.flush()
                emails_published.inc(batch_size)
                batches_flushed.inc()
                logger.info(f"✓ Published batch of {batch_size} emails to 'raw_inbox_batch'")
            
            # Clear batch and reset timer
            batch = []
            batch_size_gauge.set(0)
            last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            # Keep batch for retry or DLQ
    
    while True:
        logger.info("📥 Polling for new emails from all sources...")
        all_messages = []
        
        # Fetch from Gmail
        try:
            gmail_messages = gmail.list_messages(query="is:unread")
            logger.info(f"Gmail: {len(gmail_messages)} unread emails")
            all_messages.extend(gmail_messages)
        except Exception as e:
            logger.error(f"Gmail fetch failed: {e}")
        
        # Fetch from Outlook (if enabled)
        if outlook and outlook.enabled:
            try:
                outlook_emails = outlook.fetch_emails(since_hours=24)
                logger.info(f"Outlook: {len(outlook_emails)} emails from last 24h")
                
                # Convert to Gmail-like format for processing
                for email in outlook_emails:
                    outlook_formatted = {
                        'id': email['id'],
                        'snippet': email.get('subject', ''),
                        'labels': [],
                        'source': 'outlook'
                    }
                    all_messages.append(('outlook', email['id'], email))
            except Exception as e:
                logger.error(f"Outlook fetch failed: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # CRITICAL DEDUPLICATION LAYER
        # ═══════════════════════════════════════════════════════════
        logger.info(f"📊 Total emails fetched: {len(all_messages)}")
        
        new_messages = []
        duplicate_count = 0
        
        for item in all_messages:
            # Handle different formats (Gmail vs Outlook)
            if isinstance(item, tuple):  # Outlook message
                source, msg_id, full_msg = item
            else:  # Gmail message
                source = 'gmail'
                msg_id = item['id']
                full_msg = None  # Will fetch later if not duplicate
            
            # Check if already processed
            if is_email_processed(db_conn, msg_id):
                duplicate_count += 1
                emails_duplicates.inc()
                continue
            
            # New email - add to processing queue
            if full_msg is None and source == 'gmail':
                full_msg = gmail.get_message(msg_id)
            
            if full_msg:
                new_messages.append((source, msg_id, full_msg))
        
        logger.info(f"✓ Deduplication: {len(new_messages)} new, {duplicate_count} duplicates")
        
        # ═══════════════════════════════════════════════════════════
        # EMAIL RELEVANCE FILTERING (Save API Quota!)
        # ═══════════════════════════════════════════════════════════
        job_related_messages = []
        filtered_count = 0
        
        for source, msg_id, full_msg in new_messages:
            # Extract email content for filtering
            # For Gmail, headers are in payload.headers; for Outlook they're at top level
            subject = extract_gmail_header(full_msg, 'Subject') if source == 'gmail' else full_msg.get('subject', '')
            from_email = extract_gmail_header(full_msg, 'From') if source == 'gmail' else full_msg.get('from', '')
            
            email_for_filter = {
                'subject': subject,
                'body': full_msg.get('snippet', ''),
                'from': from_email
            }
            
            # Check if job-related
            is_job, reason, confidence = email_filter.is_job_related(email_for_filter)
            
            if is_job:
                job_related_messages.append((source, msg_id, full_msg))
                logger.debug(f"✅ Job-related: {email_for_filter['subject'][:50]} ({reason}, {confidence:.0%})")
            else:
                filtered_count += 1
                emails_filtered.labels(reason=reason).inc()
                logger.info(f"🗑️  Filtered: {email_for_filter['subject'][:50]} ({reason})")
                
                # Still mark as processed in DB to avoid re-fetching
                mark_as_processed(db_conn, msg_id, source, classification='FILTERED')
        
        # Log filter statistics
        if new_messages:
            filter_stats = email_filter.get_stats()
            spam_rate = (filtered_count / len(new_messages)) * 100 if new_messages else 0
            logger.info(
                f"📊 Filter: {len(job_related_messages)} kept, {filtered_count} filtered "
                f"({spam_rate:.1f}% spam rate) | API calls saved: {filter_stats['api_calls_saved']}"
            )
        
        # Process only job-related messages
        for source, msg_id, full_msg in job_related_messages:
            emails_processed.labels(source=source).inc()
            logger.debug(f"Processing message: {msg_id} from {source}")

            # Extract headers properly based on source
            subject = extract_gmail_header(full_msg, 'Subject') if source == 'gmail' else full_msg.get('subject', '')
            from_email = extract_gmail_header(full_msg, 'From') if source == 'gmail' else full_msg.get('from', '')
            
            # Normalize payload
            payload = {
                "message_id": full_msg.get("id"),
                "thread_id": full_msg.get("threadId"),
                "snippet": full_msg.get("snippet"),
                "subject": subject,
                "from": from_email,
                "labels": full_msg.get("labelIds", []),
                "source": source,
                "user_email": config.OUTLOOK_USER_EMAIL if source == 'outlook' else None,  # Track user for multi-tenant
                "raw_data": full_msg # Store full raw data in MinIO payload
            }

            valid, err = validate_raw_email(payload)
            if not valid:
                emails_validation_errors.inc()
                logger.error(f"Validation failed for {msg_id}: {err}")
                if producer:
                    dlq_payload = {"error": "validation_error", "details": err, "original": payload, "source": "ingestion"}
                    producer.send('dlq.raw_inbox', dlq_payload)
                    emails_dlq.inc()
                continue

            # Upload to MinIO
            try:
                # Create a path like: 2025/12/10/message_id.json
                date_prefix = time.strftime("%Y/%m/%d")
                object_name = f"{date_prefix}/{msg_id}.json"
                
                # Upload FULL raw payload to MinIO
                storage_path = storage.upload_json(object_name, payload)
                
                # Add storage path and remove heavy 'raw_data' for Kafka
                payload['storage_path'] = storage_path
                if 'raw_data' in payload:
                    del payload['raw_data']
                    
            except Exception as e:
                logger.error(f"Failed to upload to MinIO: {e}")
                # In production, you might want to DLQ this.

            # Mark as processed in database (prevents reprocessing)
            mark_as_processed(db_conn, msg_id, source, 'PENDING')
            
            # Add to batch instead of publishing immediately
            batch.append(payload)
            batch_size_gauge.set(len(batch))
            logger.debug(f"📥 Added email {msg_id} to batch (current size: {len(batch)}/{config.BATCH_SIZE})")
            
            # Check if we should flush
            if should_flush_batch():
                flush_batch()

        # Check if batch timeout is reached (even if no new emails)
        if should_flush_batch():
            flush_batch()

        time.sleep(config.POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
