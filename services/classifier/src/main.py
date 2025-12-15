print("DEBUG: Script started (line 1)")
import json
import time
import datetime
import os
import psycopg2
from typing import List, Dict
from threading import Thread
from kafka import KafkaConsumer, KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from libs.core.validation import validate_raw_email, validate_classified_event
from prometheus_client import Counter, Histogram, start_http_server
from flask import Flask, jsonify
from minio import Minio

# Import new intelligent classification system
from src.keyword_learner import KeywordLearner
from src.provider_manager import LLMClient
from src.company_extractor import CompanyExtractor
from src.role_extractor import RoleExtractor

logger = configure_logger("classifier_service")

# Prometheus metrics
events_received = Counter('classifier_events_received_total', 'Total events received')
events_validation_errors = Counter('classifier_validation_errors_total', 'Total validation errors')
events_dlq = Counter('classifier_events_dlq_total', 'Total events sent to DLQ')
events_classified = Counter('classifier_events_classified_total', 'Total events classified', ['event_type'])
keyword_matches = Counter('classifier_keyword_matches_total', 'Total keyword matches', ['classification'])
ai_classifications = Counter('classifier_ai_classifications_total', 'Total AI classifications', ['provider'])
batch_processing_time = Histogram('classifier_batch_processing_seconds', 'Time to process a batch')
batch_size_processed = Counter('classifier_batch_size_processed_total', 'Total emails in processed batches')

RATE_LIMIT_COOLDOWN_SECONDS = 60
rate_limit_state = {"until": 0.0}

class ClassifierConfig(BaseConfig):
    SERVICE_NAME: str = "classifier"
    KAFKA_GROUP_ID: str = "classifier_group_llm"

config = get_config(ClassifierConfig)

# Health check Flask app
health_app = Flask(__name__)
health_status = {"status": "starting", "last_processed": None}

@health_app.route('/health')
def health_check():
    """Health check endpoint"""
    if health_status["status"] == "healthy":
        return jsonify(health_status), 200
    else:
        return jsonify(health_status), 503

@health_app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    if health_status["status"] in ["healthy", "running"]:
        return jsonify({"status": "ready"}), 200
    else:
        return jsonify({"status": "not ready"}), 503

def start_health_server():
    """Start health check server in background thread"""
    health_app.run(host='0.0.0.0', port=8010, debug=False, use_reloader=False)

def connect_to_database():
    """Connect to PostgreSQL production database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'job_tracker_prod'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'secure_password')
        )
        logger.info("✓ Connected to production database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def get_full_email_from_minio(minio_client: Minio, storage_path: str) -> Dict:
    """Fetch full email content from MinIO storage"""
    try:
        # storage_path format: raw-emails/2025/12/15/19b1f5e1e36c68ed.json
        # Strip bucket prefix if present
        bucket_name = "raw-emails"
        object_path = storage_path.replace(f"{bucket_name}/", "", 1) if storage_path.startswith(f"{bucket_name}/") else storage_path
        
        logger.info(f"📥 Fetching from MinIO - Bucket: {bucket_name}, Path: {object_path}")
        obj = minio_client.get_object(bucket_name, object_path)
        email_data = json.loads(obj.read().decode('utf-8'))
        obj.close()
        logger.info(f"✓ Successfully fetched {len(str(email_data))} bytes from MinIO")
        return email_data
    except Exception as e:
        logger.error(f"❌ MinIO fetch failed - storage_path: {storage_path}, object_path: {object_path}, error: {e}")
        return {}

def classify_batch(db_conn, keyword_learner: KeywordLearner, llm: LLMClient, emails: List[Dict], producer: KafkaProducer, minio_client: Minio = None):
    """
    Process a batch of emails using AI-first classification:
    Layer 1: AI classification with Groq (primary method)
    Layer 2: Keyword matching (fallback when rate limited)
    Layer 3: Learning from results
    """
    batch_start = time.time()
    batch_count = len(emails)
    
    logger.info(f"🚀 Processing batch of {batch_count} emails...")
    
    classified_count = 0
    keyword_matched = 0
    ai_used = 0
    
    for idx, email_data in enumerate(emails):
        msg_id = email_data.get('message_id', email_data.get('id', 'unknown'))
        
        # Validate raw email shape
        ok, err = validate_raw_email(email_data)
        if not ok:
            events_validation_errors.inc()
            logger.error(f"Invalid email in batch: {err}")
            send_to_dlq(producer, email_data, err, "validation_error", 0)
            continue

        # Get email text - PRIORITY: Full body from MinIO > snippet
        subject = email_data.get('subject', '')
        storage_path = email_data.get('storage_path', '')
        logger.info(f"DEBUG: storage_path = '{storage_path}', minio_client exists = {minio_client is not None}")
        
        # Try to fetch full email from MinIO first
        full_email_text = ""
        if storage_path and minio_client:
            full_email_data = get_full_email_from_minio(minio_client, storage_path)
            logger.info(f"DEBUG: full_email_data type = {type(full_email_data)}, bool = {bool(full_email_data)}, keys = {list(full_email_data.keys()) if isinstance(full_email_data, dict) else 'N/A'}")
            if full_email_data:
                # Parse Gmail API format: raw_data.payload contains the email parts
                body_text = ""
                raw_data = full_email_data.get('raw_data', {})
                payload = raw_data.get('payload', {})
                logger.info(f"DEBUG: raw_data exists: {bool(raw_data)}, payload exists: {bool(payload)}")
                
                # Try to extract body from payload parts (multipart emails)
                parts = payload.get('parts', [])
                logger.info(f"DEBUG: parts count: {len(parts)}")
                for part in parts:
                    mime = part.get('mimeType', '')
                    logger.info(f"DEBUG: part mimeType: {mime}")
                    if mime == 'text/plain':
                        body_data = part.get('body', {}).get('data', '')
                        logger.info(f"DEBUG: body_data length: {len(body_data) if body_data else 0}")
                        if body_data:
                            import base64
                            try:
                                body_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                                logger.info(f"DEBUG: Successfully decoded {len(body_text)} chars from part")
                            except Exception as e:
                                logger.error(f"DEBUG: Base64 decode failed: {e}")
                            break
                
                # Fallback: try direct body field (simple emails)
                if not body_text:
                    body_data = payload.get('body', {}).get('data', '')
                    logger.info(f"DEBUG: direct body_data length: {len(body_data) if body_data else 0}")
                    if body_data:
                        import base64
                        try:
                            body_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            logger.info(f"DEBUG: Successfully decoded {len(body_text)} chars from direct body")
                        except Exception as e:
                            logger.error(f"DEBUG: Base64 decode failed: {e}")
                
                if body_text:
                    full_email_text = f"{subject}\n{body_text}"
                    logger.info(f"✓ Using full email from MinIO ({len(body_text)} chars)")
                else:
                    logger.warning(f"DEBUG: body_text is empty after all attempts")

        
        # Fallback to snippet if MinIO read failed
        if not full_email_text:
            snippet = email_data.get('snippet', email_data.get('body', ''))
            full_email_text = f"{subject}\n{snippet}"
            logger.warning(f"⚠️  Using snippet only ({len(snippet)} chars) - MinIO read failed")
        
        from_email = email_data.get('from', '')
        email_text = full_email_text
        
        if not email_text.strip():
            logger.warning(f"Empty email text for {msg_id}, skipping.")
            continue
        
        # ═══════════════════════════════════════════════════════════
        # LAYER 1: PRIMARY - AI Classification with Groq
        # ═══════════════════════════════════════════════════════════
        success = False
        ai_result = {}
        keyword_result = None
        event_type = None
        confidence = 0.0
        company = "Unknown"
        role = "General"

        # Check if we're in rate limit cooldown
        cooldown_remaining = rate_limit_state["until"] - time.time()
        if cooldown_remaining > 0:
            logger.warning(
                f"⚠️ Rate limit active, skipping AI for {msg_id} ({cooldown_remaining:.0f}s left)"
            )
        else:
            # Try AI classification
            for retry_count in range(3):
                try:
                    start_time = time.time()
                    ai_result = llm.classify(email_text)
                    duration = time.time() - start_time

                    print(f"DEBUG: Before extraction", flush=True)
                    event_type = ai_result['classification']
                    confidence = ai_result['confidence']
                    provider = ai_result.get('provider', 'unknown')
                    print(f"DEBUG: About to extract company", flush=True)
                    company = extract_company(subject, snippet, from_email, llm)
                    print(f"DEBUG: Company extracted: {company}", flush=True)
                    role = extract_role(subject, snippet, llm)
                    print(f"DEBUG: Role extracted: {role}", flush=True)

                    print(f"DEBUG AI: Company='{company}', Role='{role}'", flush=True)
                    logger.info(f"📊 Extracted - Company: '{company}', Role: '{role}'")

                    ai_classifications.labels(provider=provider).inc()
                    ai_used += 1

                    logger.info(
                        f"  ✓ AI CLASSIFY [{idx+1}/{batch_count}] {msg_id}: "
                        f"{event_type} (conf: {confidence:.2f}) - "
                        f"provider: {provider} [{duration:.2f}s]"
                    )

                    # ═══════════════════════════════════════════════
                    # LAYER 3: Learn from AI result
                    # ═══════════════════════════════════════════════
                    if confidence >= 0.90:
                        keyword_learner.learn_from_ai_classification(
                            email_text,
                            event_type,
                            confidence
                        )

                    # Record feedback
                    keyword_learner.record_classification_result(
                        msg_id,
                        'ai',
                        event_type,
                        event_type,
                        confidence
                    )

                    success = True
                    break  # Success, exit retry loop

                except Exception as e:
                    error_str = str(e).lower()
                    logger.error(f"AI classification failed for {msg_id} (attempt {retry_count + 1}/3): {e}")
                    logger.warning(f"Rate limit fallback debug: raw_error='{str(e)}', lower='{error_str}'")

                    # CRITICAL: Check if rate-limited (don't retry on rate limit)
                    if '429' in error_str or 'rate limit' in error_str:
                        rate_limit_state["until"] = time.time() + RATE_LIMIT_COOLDOWN_SECONDS
                        logger.warning(f"⚠️ Rate limit hit, falling back to keyword matching")
                        break  # Exit retry loop immediately

                    if retry_count < 2:
                        time.sleep(2 ** retry_count)  # Exponential backoff
        
        # ═══════════════════════════════════════════════════════════
        # LAYER 2: FALLBACK - Keyword matching (when rate limited)
        # ═══════════════════════════════════════════════════════════
        if not success:
            logger.warning(f"⚠️ AI unavailable for {msg_id}, falling back to keyword matching")
            
            # Try intelligent keyword matching first
            keyword_result = keyword_learner.quick_classify(email_text)
            
            if keyword_result:
                # Keyword match found!
                event_type = keyword_result['classification']
                confidence = keyword_result['confidence']
                try:
                    company = extract_company(subject, snippet, from_email, llm)
                    role = extract_role(subject, snippet, llm)
                    print(f"DEBUG KEYWORD FALLBACK: Company='{company}', Role='{role}'", flush=True)
                    logger.info(f"📊 Extracted - Company: '{company}', Role: '{role}'")
                except Exception as e:
                    print(f"DEBUG ERROR in extraction: {e}", flush=True)
                    logger.error(f"Extraction error: {e}")
                    company = "Unknown"
                    role = "General"
                
                keyword_matches.labels(classification=event_type).inc()
                keyword_matched += 1
                
                logger.info(
                    f"  ✓ KEYWORD FALLBACK [{idx+1}/{batch_count}] {msg_id}: "
                    f"{event_type} (conf: {confidence:.2f}) - "
                    f"keyword: '{keyword_result['keyword_phrase']}'"
                )
                
                # Record feedback
                keyword_learner.record_classification_result(
                    msg_id,
                    'keyword',
                    event_type,
                    event_type,
                    confidence,
                    keyword_result.get('keyword_id')
                )
                
                success = True
            else:
                # No keyword match - use basic pattern matching
                logger.warning(f"⚠️ No keyword match for {msg_id}, using basic pattern matching")
                
                # Basic keyword fallback (always works, no API needed)
                event_type = "OTHER"
                confidence = 0.65
                
                text_lower = email_text.lower()
                
                # OFFER keywords (highest priority)
                if any(kw in text_lower for kw in ["offer letter", "pleased to offer", "extend an offer", "compensation package", "employment offer", "congratulations", "we are pleased to offer"]):
                    event_type = "OFFER"
                    confidence = 0.80
                # INTERVIEW keywords
                elif any(kw in text_lower for kw in ["interview invitation", "invite you to interview", "schedule an interview", "phone screen", "zoom interview", "next steps", "technical interview", "scheduling", "interview round", "meet with", "video call", "coding challenge"]):
                    event_type = "INTERVIEW"
                    confidence = 0.80
                # REJECTION keywords
                elif any(kw in text_lower for kw in ["not moving forward", "regret to inform", "unfortunately", "other candidates", "not selected", "decided to move forward with", "pursuing other candidates", "will not be moving forward", "not the right fit", "declined", "not proceed"]):
                    event_type = "REJECTION"
                    confidence = 0.80
                # APPLIED keywords
                elif any(kw in text_lower for kw in ["thank you for applying", "application received", "application submitted", "successfully applied", "received your application", "confirm your application", "application confirmation", "applied successfully"]):
                    event_type = "APPLIED"
                    confidence = 0.75
                
                # Extract company/role with fallback
                try:
                    company = extract_company(subject, snippet, from_email, llm)
                    role = extract_role(subject, snippet, llm)
                except:
                    company = "Unknown"
                    role = "General"
                
                logger.info(
                    f"  ✓ KEYWORD FALLBACK [{idx+1}/{batch_count}] {msg_id}: "
                    f"{event_type} (conf: {confidence:.2f})"
                )
                
                keyword_matches.labels(classification=event_type).inc()
                keyword_matched += 1
        
        # ═══════════════════════════════════════════════════════════
        # POST-PROCESSING: Override OTHER→APPLIED for application confirmations
        # ═══════════════════════════════════════════════════════════
        print(f"POST-PROCESS CHECK: event_type={event_type}", flush=True)
        email_lower = email_text.lower()
        
        import sys
        sys.stderr.write(f"\n=== POST-PROCESS DEBUG ===\n")
        sys.stderr.write(f"Email text length: {len(email_lower)}\n")
        sys.stderr.write(f"Email preview: {email_lower[:300]}\n")
        sys.stderr.flush()
        
        # ═══════════════════════════════════════════════════════════
        # POST-PROCESS: Check for REJECTION keywords FIRST (highest priority)
        # ═══════════════════════════════════════════════════════════
        rejection_keywords = [
            "selected another candidate",
            "other candidates",
            "another candidate",
            "other applicants",
            "not moving forward",
            "moved forward with",
            "decided to move forward with",
            "move forward with other",
            "decided to pursue",
            "pursuing other candidates",
            "unfortunately",
            "regret to inform",
            "not selected",
            "position has been filled",
            "position filled",
            "not the right fit",
            "closer fit",
            "more closely matches",
            "will not be moving forward",
            "wish you the best",
            "best of luck in your",
            "best of luck with",
            "success in your",
            "decision is disappointing",
            "decision may be disappointing",
            "this news is disappointing",
            "not be moving forward",
            "will keep your resume on file",
            "keep you in mind for future",
            "declined",
            "unsuccessful"
        ]
        
        print(f"POST-PROCESS: Email text preview: {email_lower[:200]}...", flush=True)
        rejection_count = sum(1 for kw in rejection_keywords if kw in email_lower)
        print(f"POST-PROCESS: Rejection keyword count = {rejection_count}", flush=True)
        if rejection_count >= 1:  # Just 1 strong rejection keyword is enough
            if event_type != "REJECTION":
                logger.info(f"  🔄 POST-PROCESS: Overriding {event_type}→REJECTION (found {rejection_count} rejection keywords)")
                print(f"POST-PROCESS: OVERRIDING {event_type}→REJECTION! (keywords: {rejection_count})", flush=True)
            event_type = "REJECTION"
            confidence = max(confidence, 0.90)  # High confidence for keyword match
        
        # ═══════════════════════════════════════════════════════════
        # POST-PROCESS: If still OTHER, check for APPLIED keywords
        # ═══════════════════════════════════════════════════════════
        elif event_type == "OTHER":
            applied_keywords = [
                "application received",
                "thank you for applying",
                "application submitted",
                "we received your application",
                "reviewing your application",
                "application has been submitted",
                "application confirmation",
                "received your application",
                "application successfully submitted",
                "will review your application"
            ]
            
            print(f"POST-PROCESS: Checking {len(applied_keywords)} keywords in email", flush=True)
            if any(keyword in email_lower for keyword in applied_keywords):
                # Also check it's not an interview
                interview_keywords = ["invite you to interview", "schedule an interview"]
                has_interview = any(kw in email_lower for kw in interview_keywords)
                
                print(f"POST-PROCESS: Found APPLIED keyword! Interview={has_interview}", flush=True)
                
                if not has_interview:
                    logger.info(f"  🔄 POST-PROCESS: Overriding OTHER→APPLIED (found application confirmation keywords)")
                    print(f"POST-PROCESS: OVERRIDING to APPLIED!", flush=True)
                    event_type = "APPLIED"
                    confidence = 0.85  # High confidence for keyword match
        
        # ═══════════════════════════════════════════════════════════
        # Filter spam and invalid classifications
        # ═══════════════════════════════════════════════════════════
        print(f"FILTER CHECK: event_type='{event_type}', company='{company}', role='{role}'", flush=True)
        
        if event_type == "OTHER":
            print(f"FILTERED: event_type is OTHER", flush=True)
            events_classified.labels(event_type='OTHER').inc()
            classified_count += 1
            continue
        
        # Filter out Unknown/General companies (spam)
        if company in ['Unknown', 'General', 'N/A', '']:
            print(f"FILTERED: company is '{company}' (spam)", flush=True)
            logger.warning(f"⚠️  Filtering out spam: {event_type} for '{company}' company, role: '{role}'")
            events_classified.labels(event_type='FILTERED_SPAM').inc()
            classified_count += 1
            continue
        
        print(f"PASSED FILTER: Sending to Kafka - {company}/{role}", flush=True)

        # Construct Classified Event
        classified_event = {
            "event_id": f"cls_{msg_id}",
            "message_id": msg_id,
            "event_type": event_type,
            "company": company,
            "role": role,
            "confidence": confidence,
            "classified_at": datetime.datetime.utcnow().isoformat(),
            "user_email": email_data.get('user_email'),  # Pass through user_email for multi-tenant support
            "metadata": {
                "method": keyword_result['method'] if keyword_result else 'ai',
                "provider": ai_result.get('provider') if not keyword_result else 'keyword',
                "snippet": snippet[:200]
            },
            "research_briefing": ""
        }
        
        if event_type in ['APPLIED', 'INTERVIEW', 'OFFER', 'REJECTION']:
            producer.send('classified_events', classified_event)
            events_classified.labels(event_type=event_type).inc()
            classified_count += 1
        else:
            events_classified.labels(event_type='OTHER').inc()
            classified_count += 1
    
    batch_duration = time.time() - batch_start
    batch_processing_time.observe(batch_duration)
    batch_size_processed.inc(batch_count)
    
    efficiency_pct = (keyword_matched / batch_count * 100) if batch_count > 0 else 0
    
    logger.info(
        f"✅ Batch complete: {classified_count}/{batch_count} classified in {batch_duration:.2f}s | "
        f"Keyword: {keyword_matched} ({efficiency_pct:.1f}%) | AI: {ai_used}"
    )
    producer.flush()

# Initialize company extractor
company_extractor = CompanyExtractor()
role_extractor = RoleExtractor()

def extract_company(subject: str, snippet: str, from_email: str = "", llm_client=None) -> str:
    """Extract company name using intelligent extraction with LLM fallback"""
    company = company_extractor.extract(
        subject=subject,
        body=snippet,
        from_email=from_email
    )
    
    # If pattern-based extraction returns Unknown, try LLM
    if company == "Unknown" and llm_client:
        try:
            prompt = f"""You are extracting company names from job-related emails.

Task: Identify ONLY the company/organization name that sent this job email.

Rules:
- Return ONLY the company name (e.g., "Google", "Meta", "Microsoft")
- DO NOT return job titles or roles
- DO NOT return descriptions
- If the company name is unclear, return "Unknown"

Email:
Subject: {subject[:200]}
From: {from_email}
Body: {snippet[:300]}

Company name (one or two words only):"""
            
            response = llm_client.provider_manager.make_api_call(
                llm_client.provider_manager.select_best_provider(),
                prompt
            )
            
            if response['success']:
                extracted = response['content'].strip().strip('"\'.,').strip()
                # Validate it's a reasonable company name (not a sentence or role)
                words = extracted.split()
                if extracted and len(words) <= 3 and len(extracted) > 2 and len(extracted) < 50:
                    # Filter out spam and role titles
                    spam_keywords = ['credit card', 'loan', 'bank', 'hdfc', 'tata', 'offer', 'eligible', 'engineer', 'manager', 'developer', 'analyst', 'specialist']
                    if not any(spam in extracted.lower() for spam in spam_keywords):
                        logger.info(f"LLM extracted company: {extracted}")
                        return extracted
        except Exception as e:
            logger.debug(f"LLM company extraction failed: {e}")
    
    return company

def extract_role(subject: str, snippet: str, llm_client=None) -> str:
    """Extract job role/title using intelligent extractor with LLM fallback"""
    role = role_extractor.extract(subject=subject, body=snippet)
    
    # If pattern-based extraction returns General, try LLM
    if role == "General" and llm_client:
        try:
            prompt = f"""You are extracting job titles from job-related emails.

Task: Identify ONLY the job role/position/title being offered or interviewed for.

Rules:
- Return ONLY the job title (e.g., "Software Engineer", "Product Manager", "Data Scientist")
- DO NOT return company names
- DO NOT return descriptions
- Include seniority level if mentioned (e.g., "Senior", "Staff", "Principal")
- If the role is unclear, return "General"

Email:
Subject: {subject[:200]}
Body: {snippet[:300]}

Job title (3-6 words max):"""
            
            response = llm_client.provider_manager.make_api_call(
                llm_client.provider_manager.select_best_provider(),
                prompt
            )
            
            if response['success']:
                extracted = response['content'].strip().strip('"\'.,').strip()
                # Validate it's a reasonable role (not a company name or sentence)
                words = extracted.split()
                if extracted and len(words) <= 6 and len(extracted) > 3 and len(extracted) < 80:
                    # Filter out company names that might have been returned
                    company_keywords = ['google', 'meta', 'amazon', 'microsoft', 'apple', 'netflix', 'tesla', 'uber', 'spacex']
                    if not any(company in extracted.lower() for company in company_keywords):
                        logger.info(f"LLM extracted role: {extracted}")
                        return extracted
        except Exception as e:
            logger.debug(f"LLM role extraction failed: {e}")
    
    return role

def send_to_dlq(producer: KafkaProducer, email_data: Dict, error: str, error_type: str, retry_count: int):
    """Send failed email to Dead Letter Queue"""
    try:
        dlq_message = {
            "error": error_type,
            "details": error,
            "original": email_data,
            "source": "classifier",
            "retry_count": retry_count,
            "failed_at": datetime.datetime.utcnow().isoformat()
        }
        producer.send('dlq.classifier', dlq_message)
        events_dlq.inc()
        logger.warning(f"📮 Sent to DLQ: {email_data.get('message_id', 'unknown')} - {error_type}")
    except Exception as e:
        logger.error(f"Failed to send to DLQ: {e}")

def main():
    logger.info("=" * 80)
    logger.info("🚀 Starting Intelligent Classifier Service v2.0")
    logger.info("=" * 80)
    logger.info("Features:")
    logger.info("  ✓ Layer 1: Keyword matching (instant, free)")
    logger.info("  ✓ Layer 2: Multi-provider AI (Groq, Together, Gemini)")
    logger.info("  ✓ Layer 3: Self-learning from results")
    logger.info("=" * 80)
    
    # Start health check server in background
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    logger.info("Health check server started on :8010/health")
    
    # Start Prometheus metrics server
    start_http_server(8002)
    logger.info("Prometheus metrics available at :8002/metrics")
    
    # Connect to production database
    logger.info("Connecting to production database...")
    try:
        db_conn = connect_to_database()
        health_status["status"] = "running"
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return
    
    # Initialize Keyword Learner
    logger.info("Initializing KeywordLearner...")
    try:
        keyword_learner = KeywordLearner(db_conn)
        stats = keyword_learner.get_statistics()
        logger.info(f"  ✓ Loaded {stats.get('active_keywords', 0)} active keywords")
        logger.info(f"  ✓ Total matches: {stats.get('total_matches', 0)}")
        logger.info(f"  ✓ Average accuracy: {stats.get('avg_accuracy', 0):.2%}")
    except Exception as e:
        logger.error(f"Failed to initialize KeywordLearner: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return
    
    # Initialize Multi-Provider LLM Client
    logger.info("Initializing Multi-Provider LLM Client...")
    try:
        llm = LLMClient(db_conn)
        logger.info("  ✓ LLM Client initialized with intelligent provider routing")
        health_status["status"] = "running"
    except Exception as e:
        logger.error(f"Failed to initialize LLM Client: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return
    
    # Initialize MinIO Client
    logger.info("Initializing MinIO Client...")
    try:
        minio_client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'minio:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minio_admin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minio_password'),
            secure=False
        )
        logger.info("  ✓ MinIO Client initialized for full email retrieval")
    except Exception as e:
        logger.warning(f"Failed to initialize MinIO Client: {e} - will use snippets only")
        minio_client = None

    # Wait for Kafka - listen to BOTH topics
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'raw_inbox_stream',      # Old single-email topic
                'raw_inbox_batch',       # New batch topic
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'  # Process from beginning when consumer group is new
            )
            logger.info("Kafka Consumer connected to 'raw_inbox_stream' and 'raw_inbox_batch'")
            health_status["status"] = "healthy"
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = f"Kafka connection: {e}"
            time.sleep(5)

    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    logger.info("Listening for messages...")
    
    # Periodically cleanup low-accuracy keywords (every 100 messages)
    message_count = 0
    
    try:
        for message in consumer:
            topic = message.topic
            data = message.value
            events_received.inc()
            message_count += 1
            
            # Update health status
            health_status["last_processed"] = datetime.datetime.utcnow().isoformat()
            health_status["status"] = "healthy"
            
            # Periodic keyword cleanup
            if message_count % 100 == 0:
                logger.info("Running periodic keyword cleanup...")
                keyword_learner.deactivate_low_accuracy_keywords()
            
            if topic == 'raw_inbox_batch':
                # Process batch
                emails = data.get('emails', [])
                count = data.get('count', len(emails))
                logger.info(f"📦 Received batch from 'raw_inbox_batch': {count} emails")
                
                if emails:
                    classify_batch(db_conn, keyword_learner, llm, emails, producer, minio_client)
                    try:
                        consumer.commit()
                    except Exception as commit_error:
                        logger.error(f"Failed to commit batch offsets: {commit_error}")
            
            else:
                # Process single email (backward compatibility)
                email_data = data
                msg_id = email_data.get('message_id', email_data.get('id', 'unknown'))
                logger.info(f"📧 Received single email from 'raw_inbox_stream': {msg_id}")
                
                classify_batch(db_conn, keyword_learner, llm, [email_data], producer, minio_client)
                try:
                    consumer.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to commit stream offsets: {commit_error}")
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        raise
    finally:
        if db_conn:
            db_conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()
