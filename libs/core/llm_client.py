import json
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("llm_client")

class LLMConfig(BaseConfig):
    SERVICE_NAME: str = "classifier"
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # "openai", "groq", "gemini", or "auto"

config = get_config(LLMConfig)

# Abstract Base Class
class LLMProvider:
    def classify(self, email_content: str) -> str:
        raise NotImplementedError
    
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

# OpenAI Provider (Primary - Most Reliable)
class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Fast, cheap, reliable
        logger.info(f"OpenAI Provider initialized with model: {self.model}")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze the following email snippet and determine if it is a career-related event.
Return ONLY a JSON object with:
- event_type: "APPLIED", "INTERVIEW", "OFFER", "REJECTION", or "OTHER"
  * APPLIED: Confirmation that you applied to a job (application received, submitted)
  * INTERVIEW: Interview invitation or scheduling
  * OFFER: Job offer received (ready to join, compensation details)
  * REJECTION: Application rejected
  * OTHER: Not career-related
- company: Company name (if applicable)
- confidence: 0.0 to 1.0
- summary: Brief summary

Email Snippet:
{email_content}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI inference failed: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

# Groq Provider (Fast & High Quota - PRODUCTION PRIMARY)
class GroqProvider(LLMProvider):
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"  # Fast and accurate for classification
        logger.info(f"🚀 Groq Provider initialized with model: {self.model}")
        logger.info(f"📊 Groq quota: 14,400 requests/day, 30 requests/minute")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze this email and classify the job application event type.

Return ONLY a JSON object with these fields:
- event_type: Must be one of: "APPLIED", "INTERVIEW", "OFFER", "REJECTION", "OTHER"
- company: Company name
- confidence: 0.0 to 1.0
- summary: Brief summary

EVENT TYPE RULES:

APPLIED - Use this when YOU applied and THEY confirm they received it:
  Examples: "Thank you for applying", "Application received", "We received your application", 
  "Your application has been submitted", "Reviewing your application", "Application confirmation"
  
INTERVIEW - Use this when THEY invite YOU to interview:
  Examples: "Invite you to interview", "Schedule an interview", "Interview invitation",
  "Phone screen", "Technical round", "Onsite interview"
  
OFFER - Use this when THEY offer YOU the job:
  Examples: "Offer letter", "Pleased to extend an offer", "Congratulations", 
  "Compensation package", "Welcome to the team"
  
REJECTION - Use this when THEY reject YOUR application:
  Examples: "Unfortunately", "Not moving forward", "Other candidates", 
  "Not selected", "Decided to pursue other applicants"
  
OTHER - Use this for everything else:
  Examples: Marketing emails, company newsletters, spam, unrelated content

Email to classify:
{email_content}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq inference failed: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

# Gemini Provider (Fallback - Quota Limited but supports multi-key rotation)
class GeminiProvider(LLMProvider):
    def __init__(self):
        # Support comma-separated keys: KEY1,KEY2,KEY3
        if not config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required")
        
        self.api_keys = [k.strip() for k in config.GOOGLE_API_KEY.split(',') if k.strip()]
        self.current_key_index = 0
        self.last_request_time = 0  # Track last request for rate limiting
        self.min_request_interval = 4.0  # 15 req/min = 1 req every 4 seconds
        
        logger.info(f"Gemini Provider initialized with {len(self.api_keys)} API key(s)")
        logger.info(f"⏱️  Rate limit: {self.min_request_interval}s between requests (15 RPM)")
        
        # Initialize with first key
        genai.configure(api_key=self.api_keys[0])
        # Use the latest Gemini model (verified working in test_real_apis.py)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _rotate_key(self):
        """Rotate to next API key on quota exhaustion"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=new_key)
        logger.info(f"Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def classify(self, email_content: str) -> str:
        prompt = f"""Analyze this job application email and classify it. Return ONLY a JSON object with this exact structure:
{{
    "event_type": "APPLIED|INTERVIEW|OFFER|REJECTION|OTHER",
    "company": "company name",
    "confidence": 0.0-1.0,
    "summary": "brief summary"
}}

Classification Rules:
- APPLIED: Confirmation that you APPLIED/SUBMITTED an application ("application received", "thank you for applying", "application submitted", "we received your application", "reviewing your application", "application confirmation")
- INTERVIEW: Interview invitation or scheduling ("invite you to interview", "schedule an interview", "phone screen", "technical round", "onsite interview")
- OFFER: Job offer with compensation details ("congratulations", "pleased to extend an offer", "offer letter", "compensation package", "welcome to the team")
- REJECTION: Application rejected ("unfortunately", "not moving forward", "other candidates", "not selected", "application status: rejected")
- OTHER: Not career-related (spam, marketing emails, general company updates, newsletters, unrelated content)

Email to classify:
{email_content}

Return ONLY the JSON object, no other text."""
        return self.generate(prompt, json_mode=True)

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        import time
        
        # Rate limiting: ensure minimum time between requests
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"⏸️  Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        # Try all keys before giving up
        attempts = 0
        max_attempts = len(self.api_keys)
        
        generation_config = {"response_mime_type": "application/json"} if json_mode else {}

        while attempts < max_attempts:
            try:
                self.last_request_time = time.time()
                response = self.model.generate_content(
                    prompt, 
                    generation_config=generation_config
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                # Check if quota exceeded or rate limit
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    attempts += 1
                    # Exponential backoff: 5s, 10s, 20s, 40s...
                    backoff_time = min(5 * (2 ** attempts), 60)  # Max 60s
                    logger.warning(f"⚠️  Rate limit hit on key #{self.current_key_index + 1}, waiting {backoff_time}s...")
                    time.sleep(backoff_time)
                    
                    if attempts < max_attempts:
                        logger.warning(f"Rotating to next API key...")
                        self._rotate_key()
                        continue
                    else:
                        logger.error(f"All {max_attempts} API keys exhausted")
                        raise
                else:
                    # Non-quota error, don't rotate
                    logger.error(f"Gemini inference failed: {e}")
                    raise

# Mock Provider (Testing Only)
class MockProvider(LLMProvider):
    def __init__(self):
        logger.info("Mock Provider initialized (testing mode)")
    
    def classify(self, email_content: str) -> str:
        # Parse email content to extract event type
        email_lower = email_content.lower()
        
        # Debug logging
        logger.info(f"[MockProvider] Classifying email snippet: {email_content[:100]}...")
        
        # Determine event type based on content (order matters!)
        if any(keyword in email_lower for keyword in ['application received', 'thank you for applying', 'application submitted', 'we received your application', "we've received your application", 'application confirmation', 'your application for']):
            event_type = "APPLIED"
            logger.info(f"[MockProvider] Matched APPLIED")
        elif any(keyword in email_lower for keyword in ['interview', 'scheduled', 'meeting', 'technical round', 'onsite', 'invitation']):
            event_type = "INTERVIEW"
            logger.info(f"[MockProvider] Matched INTERVIEW")
        elif any(keyword in email_lower for keyword in ['offer', 'congratulations', 'pleased to extend', 'job offer', 'compensation package', 'ready to join', 'start date']):
            event_type = "OFFER"
            logger.info(f"[MockProvider] Matched OFFER")
        elif any(keyword in email_lower for keyword in ['unfortunately', 'not moving forward', 'decided to', 'other candidates', 'regret', 'application status']):
            event_type = "REJECTION"
            logger.info(f"[MockProvider] Matched REJECTION")
        else:
            event_type = "OTHER"
            logger.info(f"[MockProvider] Matched OTHER (no keywords found)")
        
        # Extract company name - try multiple strategies
        company = "Unknown"
        
        # Strategy 1: Look for " at CompanyName" pattern in subject/body
        import re
        at_match = re.search(r'\bat\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', email_content)
        if at_match:
            company = at_match.group(1)
        
        # Strategy 2: Extract from email domain if company not found
        if company == "Unknown":
            email_match = re.search(r'@([a-zA-Z]+)\.com', email_content)
            if email_match:
                company = email_match.group(1).capitalize()
        
        # Strategy 3: Look for common company name patterns
        if company == "Unknown":
            companies = ['Google', 'Amazon', 'Microsoft', 'Meta', 'Apple', 'Netflix', 
                        'Airbnb', 'Stripe', 'Databricks', 'Snowflake', 'Uber', 'Lyft']
            for comp in companies:
                if comp.lower() in email_lower:
                    company = comp
                    break
        
        return json.dumps({
            "event_type": event_type,
            "company": company,
            "confidence": 0.95,
            "summary": f"Mock classification: {event_type} from {company}"
        })

    def generate(self, prompt: str) -> str:
        return "Mock generated content based on prompt."

# Main Client with Auto-Fallback
class LLMClient:
    def __init__(self):
        self.providers = []
        
        # Initialize providers based on config
        if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
            try:
                self.providers.append(("OpenAI", OpenAIProvider()))
            except Exception as e:
                logger.warning(f"Failed to init OpenAI: {e}")
        
        if config.LLM_PROVIDER == "groq" and config.GROQ_API_KEY:
            try:
                self.providers.append(("Groq", GroqProvider()))
            except Exception as e:
                logger.warning(f"Failed to init Groq: {e}")
        
        if config.LLM_PROVIDER == "gemini" and config.GOOGLE_API_KEY:
            try:
                self.providers.append(("Gemini", GeminiProvider()))
            except Exception as e:
                logger.warning(f"Failed to init Gemini: {e}")
        
        # Auto mode: try OpenAI first, then Groq, then Gemini
        if config.LLM_PROVIDER == "auto":
            if config.OPENAI_API_KEY:
                try:
                    self.providers.append(("OpenAI", OpenAIProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init OpenAI: {e}")
            if config.GROQ_API_KEY:
                try:
                    self.providers.append(("Groq", GroqProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init Groq: {e}")
            if config.GOOGLE_API_KEY:
                try:
                    self.providers.append(("Gemini", GeminiProvider()))
                except Exception as e:
                    logger.warning(f"Failed to init Gemini: {e}")
        
        if config.LLM_PROVIDER == "mock":
            self.providers.append(("Mock", MockProvider()))
        
        if not self.providers:
            logger.error("No LLM providers available!")
            raise ValueError("At least one LLM provider must be configured")
        
        logger.info(f"Initialized {len(self.providers)} provider(s): {[name for name, _ in self.providers]}")
    
    def classify_email(self, email_content: str) -> str:
        last_error = None
        
        for provider_name, provider in self.providers:
            try:
                logger.info(f"Attempting classification with {provider_name}...")
                result = provider.classify(email_content)
                logger.info(f"Successfully classified with {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        logger.error(f"All providers failed. Last error: {last_error}")
        return None

    def generate_text(self, prompt: str) -> str:
        last_error = None
        
        for provider_name, provider in self.providers:
            try:
                logger.info(f"Attempting generation with {provider_name}...")
                result = provider.generate(prompt)
                logger.info(f"Successfully generated with {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue
        
        logger.error(f"All providers failed generation. Last error: {last_error}")
        return None
