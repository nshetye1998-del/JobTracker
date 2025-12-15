import json
import time
import os
import psycopg2
from kafka import KafkaConsumer, KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from libs.core.validation import validate_classified_event
from libs.core.llm_client import LLMClient
from prometheus_client import Counter, start_http_server
from multi_provider_manager import MultiProviderResearchManager
from local_research_fallback import LocalResearchFallback

logger = configure_logger("researcher_service")

# Prometheus metrics
events_received = Counter('researcher_events_received_total', 'Total events received')
events_validation_errors = Counter('researcher_validation_errors_total', 'Total validation errors')
events_dlq = Counter('researcher_events_dlq_total', 'Total events sent to DLQ')
research_completed = Counter('researcher_research_completed_total', 'Total research completed')
research_failed = Counter('researcher_research_failed_total', 'Total research failures')
events_skipped = Counter('researcher_events_skipped_total', 'Total events skipped (non-interview/offer)')

class ResearcherConfig(BaseConfig):
    SERVICE_NAME: str = "researcher"
    KAFKA_GROUP_ID: str = "researcher_group"

config = get_config(ResearcherConfig)

from libs.core.db import DatabaseClient

# ... (imports)

def create_fallback_research(company: str, role: str, event_type: str) -> str:
    """
    Create a general formatted response when research APIs are exhausted
    """
    return f"""📋 {company} - {role}

🎯 Event Type: {event_type}

ℹ️ Research services are temporarily unavailable. Here's what we know:

**Company:** {company}
**Position:** {role}

✅ Next Steps:
• Research the company on LinkedIn and Glassdoor
• Review the job description carefully
• Prepare questions about the role and team
• Research the company's recent news and products
• Practice relevant technical concepts

💡 General Preparation Tips:
• Review your resume and be ready to discuss your experience
• Prepare STAR method examples for behavioral questions
• Research the company's tech stack and products
• Prepare 2-3 thoughtful questions for the interviewer
• Test your setup if it's a virtual interview

Good luck with your application! 🚀"""


def format_research_with_llm(company: str, role: str, research_result: dict, llm_client: LLMClient) -> str:
    """
    Use LLM to format research into structured, detailed briefing
    """
    # Extract sources from research result
    sources = research_result.get("sources", [])
    company_info = research_result.get("company_info", "")
    
    # DEBUG: Check what sources contains
    logger.debug(f"DEBUG sources type: {type(sources)}, length: {len(sources) if isinstance(sources, list) else 'N/A'}")
    if sources and len(sources) > 0:
        logger.debug(f"DEBUG first source type: {type(sources[0])}, value: {sources[0]}")
    
    # Combine source information
    source_text_parts = []
    for i, s in enumerate(sources[:5]):
        if isinstance(s, dict):
            source_text_parts.append(f"Source {i+1}: {s.get('title', 'N/A')}\n{s.get('snippet', '')}")
        elif isinstance(s, str):
            source_text_parts.append(f"Source {i+1}: {s}")
        else:
            logger.warning(f"Unexpected source type: {type(s)}")
    
    source_text = "\n\n".join(source_text_parts)
    
    if not source_text:
        source_text = f"Limited information available for {company}"
    
    prompt = f"""Format the following company research into a structured WhatsApp message briefing.

Company: {company}
Role: {role}

Research Sources:
{source_text}

Create a concise, well-formatted briefing with:
1. Company overview (1-2 sentences)
2. Key highlights (3-5 bullet points about products, market position, culture)
3. Interview process overview (if mentioned)
4. Compensation/benefits info (if mentioned)
5. Preparation tips for this role

Format with emojis and bullets for WhatsApp readability.
Keep it under 500 words but information-dense.
Use this structure:

[Company Name] is [brief description].

🎯 Key Highlights:
• [highlight 1]
• [highlight 2]
• [highlight 3]

💼 Interview Process:
[process info if available, or general tech interview info]

💰 Compensation:
[comp info if available]

✅ Preparation Tips:
• [tip 1]
• [tip 2]

Be specific with numbers, market share, and concrete facts from the sources."""

    try:
        response = llm_client.generate_text(prompt)
        if response:
            return response.strip()
        else:
            logger.warning("LLM returned None, using fallback")
            raise ValueError("Empty LLM response")
    except Exception as e:
        logger.error(f"LLM formatting failed: {e}")
        # Fallback to basic format
        basic_format = f"{company}\n\n"
        for i, source in enumerate(sources[:3]):
            basic_format += f"• {source.get('snippet', '')[:100]}...\n"
        return basic_format or f"{company} - Technology company"


def main():
    logger.info("Starting Multi-Provider Researcher Service...")
    
    # Start Prometheus metrics server
    start_http_server(8003)
    logger.info("Prometheus metrics available at :8003/metrics")
    
    # Connect to PostgreSQL for multi-provider tracking
    db_conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "job_tracker_prod"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password")
    )
    
    # Initialize multi-provider manager
    research_manager = MultiProviderResearchManager(db_conn)
    db = DatabaseClient(config)
    llm_client = LLMClient()
    
    # Initialize local research fallback
    local_fallback = LocalResearchFallback(db_conn)
    
    # Log cache statistics
    stats = local_fallback.get_cache_stats()
    logger.info(f"📊 Research Cache Stats:")
    logger.info(f"   Total researches: {stats['total_cached']}")
    logger.info(f"   Unique companies: {stats['unique_companies']}")
    logger.info(f"   Unique roles: {stats['unique_roles']}")
    if stats['most_recent']:
        logger.info(f"   Most recent: {stats['most_recent']}")
    
    # Wait for Kafka
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'classified_events',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest',
                max_poll_interval_ms=900000,  # 15 minutes
                max_poll_records=5,
                session_timeout_ms=60000,
                heartbeat_interval_ms=20000
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)

    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    logger.info("Listening for classified events...")
    
    research_count = 0
    skipped_count = 0
    cache_hits = 0
    live_api_calls = 0
    
    for message in consumer:
        event = message.value
        events_received.inc()
        logger.info(f"Received event: {event.get('event_type')} for {event.get('company')}")

        # Basic validation
        ok, err = validate_classified_event({
            "event_id": event.get("event_id", event.get("original_email_id", "")),
            "message_id": event.get("original_email_id", ""),
            "event_type": event.get("event_type", "UNKNOWN"),
            "company": event.get("company"),
            "role": event.get("role"),
            "confidence": float(event.get("confidence", 0.0)),
            "classified_at": event.get("classified_at"),
            "metadata": event.get("metadata"),
            "research_briefing": event.get("research_briefing"),
        })
        if not ok:
            events_validation_errors.inc()
            logger.error(f"Invalid classified event: {err}")
            producer.send('dlq.classified_events', {
                "error": "invalid_classified_event",
                "details": err,
                "original": event,
                "source": "researcher"
            })
            events_dlq.inc()
            continue
        
        # FILTER: Only research INTERVIEW and OFFER events
        event_type = event.get('event_type', 'UNKNOWN')
        if event_type not in ['INTERVIEW', 'OFFER']:
            logger.info(f"⏭️  Skipping research for {event_type} event")
            events_skipped.inc()
            skipped_count += 1
            
            # Persist without research
            if event.get('company'):
                event['research_briefing'] = f"No research needed for {event_type} events"
                try:
                    db.upsert_application(event)
                    logger.info("Persisted application (no research)")
                except Exception as e:
                    logger.error(f"Failed to persist: {e}")
                
                # Ensure notification has required 'id' field for dashboard-API
                notification_event = event.copy()
                if 'id' not in notification_event:
                    notification_event['id'] = event.get('event_id') or event.get('original_email_id')
                
                producer.send('notifications', notification_event)
            continue
        
        # Research with multi-provider system
        if event.get('company'):
            company = event['company']
            role = event.get('role')
            
            logger.info(f"🔍 Researching: {company} - {role} ({event_type})")
            
            try:
                # TIER 1: Try live API research
                result = research_manager.research_company(company, role)
                
                if result["success"]:
                    # SUCCESS: Save to cache for future use
                    local_fallback.save_research(
                        company=company,
                        role=role or "General",
                        research_data=result.get("company_info", {}),
                        source=result.get("provider", "unknown")
                    )
                    
                    # Use LLM to format detailed research briefing
                    logger.info(f"📝 Formatting research with LLM...")
                    briefing = format_research_with_llm(
                        company=company,
                        role=role,
                        research_result=result,
                        llm_client=llm_client
                    )
                    
                    event['research_briefing'] = briefing
                    research_completed.inc()
                    research_count += 1
                    live_api_calls += 1
                    
                    # Save to research_cache database table
                    try:
                        company_info = result.get("company_info", {})
                        db.save_research_cache(
                            company=company,
                            role=role or "General",
                            description=briefing,
                            data_source=result.get("provider", "unknown"),
                            research_quality=1.0,  # Live API research is highest quality
                            salary_range=company_info.get("salary_range"),
                            industry=company_info.get("industry"),
                            company_size=company_info.get("company_size")
                        )
                        logger.info(f"💾 Saved to research_cache table")
                    except Exception as e:
                        logger.error(f"Failed to save research_cache: {e}")
                    
                    logger.info(f"✅ Live research: {company} (via {result['provider']})")
                else:
                    # TIER 2: APIs exhausted - use intelligent fallback
                    research_failed.inc()
                    logger.warning(f"⚠️ All APIs exhausted, using cache fallback")
                    
                    fallback_result = local_fallback.generate_fallback_research(company, role or "General")
                    
                    # Format fallback using LLM if available
                    briefing = fallback_result.get('company_info', {}).get('description', '')
                    event['research_briefing'] = briefing
                    
                    cache_hits += 1
                    research_count += 1
                    
                    # Save fallback research to database
                    try:
                        company_info = fallback_result.get('company_info', {})
                        quality = company_info.get('quality', 0.4)
                        match_type = fallback_result.get('match_type', 'generic_template')
                        
                        db.save_research_cache(
                            company=company,
                            role=role or "General",
                            description=briefing,
                            data_source=f"fallback_{match_type}",
                            research_quality=quality,
                            salary_range=company_info.get("salary_range"),
                            industry=company_info.get("industry"),
                            company_size=company_info.get("company_size")
                        )
                        logger.info(f"💾 Saved fallback to research_cache table")
                    except Exception as e:
                        logger.error(f"Failed to save fallback research_cache: {e}")
                    
                    match_type = fallback_result.get('match_type', 'unknown')
                    quality = fallback_result.get('company_info', {}).get('quality', 0)
                    logger.info(f"✅ Fallback research: {company} ({match_type}, quality: {quality:.0%})")
                
                # Persist to database
                try:
                    db.upsert_application(event)
                    logger.info("Persisted application to Postgres")
                except Exception as e:
                    logger.error(f"Failed to persist: {e}")
                
                # Send to notifications with required 'id' field
                notification_event = event.copy()
                if 'id' not in notification_event:
                    notification_event['id'] = event.get('event_id') or event.get('original_email_id')
                
                producer.send('notifications', notification_event)
                
                # Log stats every 10 applications
                if (research_count + skipped_count) % 10 == 0:
                    total = research_count + skipped_count
                    savings_pct = (skipped_count / total * 100) if total > 0 else 0
                    cache_rate = (cache_hits / research_count * 100) if research_count > 0 else 0
                    
                    logger.info(f"""
📊 RESEARCH STATISTICS:
═══════════════════════════════════════
Total processed: {total}
Researched: {research_count}
Skipped: {skipped_count}
Live API calls: {live_api_calls}
Cache hits: {cache_hits} ({cache_rate:.1f}%)
API savings: {savings_pct:.1f}%
═══════════════════════════════════════
                    """)
                    
                    # Log provider stats
                    provider_stats = research_manager.get_provider_stats()
                    logger.info("📊 PROVIDER USAGE:")
                    for provider, stats in provider_stats.items():
                        logger.info(f"  {provider}: {stats['daily_usage']}/{stats['daily_limit']} "
                                  f"(available: {stats['available']})")
                    
                    # Log cache stats
                    cache_stats = local_fallback.get_cache_stats()
                    logger.info(f"💾 CACHE STATUS: {cache_stats['total_cached']} total, "
                              f"{cache_stats['unique_companies']} companies, "
                              f"{cache_stats['unique_roles']} roles")
            
            except Exception as e:
                research_failed.inc()
                logger.error(f"Research error: {e}")
                
                # Use intelligent fallback on exception
                try:
                    fallback_result = local_fallback.generate_fallback_research(company, role or "General")
                    briefing = fallback_result.get('company_info', {}).get('description', '')
                    event['research_briefing'] = briefing
                    cache_hits += 1
                    
                    # Save error fallback to database
                    try:
                        company_info = fallback_result.get('company_info', {})
                        quality = company_info.get('quality', 0.4)
                        match_type = fallback_result.get('match_type', 'generic_template')
                        
                        db.save_research_cache(
                            company=company,
                            role=role or "General",
                            description=briefing,
                            data_source=f"error_fallback_{match_type}",
                            research_quality=quality,
                            salary_range=company_info.get("salary_range"),
                            industry=company_info.get("industry"),
                            company_size=company_info.get("company_size")
                        )
                        logger.info(f"💾 Saved error fallback to research_cache")
                    except Exception as db_err:
                        logger.error(f"Failed to save error fallback: {db_err}")
                    
                    logger.info(f"📋 Using cache fallback due to error")
                except Exception as fb_error:
                    logger.error(f"Fallback also failed: {fb_error}")
                    event['research_briefing'] = create_fallback_research(
                        company=company,
                        role=role or "General",
                        event_type=event_type
                    )
                    logger.info(f"📋 Using basic fallback format")
                
                # Send to notifications with required 'id' field
                notification_event = event.copy()
                if 'id' not in notification_event:
                    notification_event['id'] = event.get('event_id') or event.get('original_email_id')
                
                producer.send('notifications', notification_event)
        else:
            logger.warning("No company name found in event.")
        
        # Rate limiting: 15 seconds between researches (balanced for fallback processing)
        time.sleep(15)

if __name__ == "__main__":
    main()
