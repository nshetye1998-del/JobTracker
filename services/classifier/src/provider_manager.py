"""
ProviderManager: Intelligent Multi-Provider LLM Routing

This module implements intelligent routing across multiple LLM providers:
1. Groq (primary) - Fast, 14,400 requests/day, FREE
2. OpenRouter (backup #1) - 1,000 requests/day, FREE (no credit card)
3. Hugging Face (backup #2) - 24,000 requests/day, FREE FOREVER (no credit card)

ALL PROVIDERS ARE 100% FREE - NO CREDIT CARDS REQUIRED! 🎉

Features:
- Automatic quota tracking
- Performance monitoring
- Intelligent provider selection based on:
  * Available quota
  * Recent success rate
  * Response latency
  * Provider priority
- Never exhausts quota (fails over automatically)
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Intelligent multi-provider routing system
    """
    
    def __init__(self, db_conn):
        """
        Initialize provider manager
        
        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn
        self.providers = self.initialize_providers()
        logger.info(f"ProviderManager initialized with {len(self.providers)} providers")
    
    def initialize_providers(self) -> Dict:
        """
        Initialize all available providers based on environment variables
        
        Returns:
            Dictionary of provider configurations
        """
        providers = {}
        
        # Groq (primary - fast and free tier friendly)
        if os.getenv('GROQ_API_KEY'):
            providers['groq'] = {
                'name': 'groq',
                'api_key': os.getenv('GROQ_API_KEY'),
                'endpoint': 'https://api.groq.com/openai/v1/chat/completions',
                'model': 'llama-3.1-8b-instant',
                'daily_limit': int(os.getenv('GROQ_DAILY_LIMIT', 14400)),
                'priority': 1,
                'type': 'openai_compatible'
            }
            logger.info("✓ Groq provider configured (FREE, 14,400/day)")
        
        # OpenRouter (backup #1 - FREE, no credit card needed!)
        if os.getenv('OPENROUTER_API_KEY'):
            providers['openrouter'] = {
                'name': 'openrouter',
                'api_key': os.getenv('OPENROUTER_API_KEY'),
                'endpoint': 'https://openrouter.ai/api/v1/chat/completions',
                'model': 'meta-llama/llama-3.1-8b-instruct:free',
                'daily_limit': int(os.getenv('OPENROUTER_DAILY_LIMIT', 1000)),
                'priority': 2,
                'type': 'openai_compatible'
            }
            logger.info("✓ OpenRouter provider configured (FREE, 1,000/day, NO CREDIT CARD)")
        
        # Hugging Face (backup #2 - FREE FOREVER!)
        if os.getenv('HUGGINGFACE_TOKEN'):
            providers['huggingface'] = {
                'name': 'huggingface',
                'api_key': os.getenv('HUGGINGFACE_TOKEN'),
                'endpoint': 'https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct/v1/chat/completions',
                'model': 'meta-llama/Meta-Llama-3-8B-Instruct',
                'daily_limit': int(os.getenv('HUGGINGFACE_DAILY_LIMIT', 24000)),  # 1000/hour * 24
                'priority': 3,
                'type': 'openai_compatible'
            }
            logger.info("✓ Hugging Face provider configured (FREE FOREVER, 24,000/day, NO CREDIT CARD)")
        
        # Gemini (optional - requires Google account)
        if os.getenv('GOOGLE_API_KEY'):
            providers['gemini'] = {
                'name': 'gemini',
                'api_key': os.getenv('GOOGLE_API_KEY'),
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                'model': 'gemini-pro',
                'daily_limit': int(os.getenv('GEMINI_DAILY_LIMIT', 1500)),
                'priority': 4,
                'type': 'gemini'
            }
            logger.info("✓ Gemini provider configured (1,500/day)")
        
        if not providers:
            logger.error("No LLM providers configured! Please set API keys in environment.")
        
        return providers
    
    def get_quota_usage_today(self, provider_name: str) -> int:
        """
        Get today's quota usage for provider
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Number of calls made today
        """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT calls_made
                FROM daily_quota_usage
                WHERE date = CURRENT_DATE
                AND provider_name = %s
            """, (provider_name,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting quota usage: {e}")
            return 0
    
    def get_provider_performance(self, provider_name: str, hours: int = 1) -> Dict:
        """
        Get recent performance metrics for provider
        
        Args:
            provider_name: Name of the provider
            hours: Number of hours to look back
            
        Returns:
            Performance statistics dictionary
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
                    AVG(latency_ms) as avg_latency,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM provider_performance
                WHERE provider_name = %s
                AND timestamp > NOW() - INTERVAL '%s hours'
            """, (provider_name, hours))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result and result['total_calls'] > 0:
                # Convert Decimal to float to avoid type errors
                return {
                    'total_calls': int(result['total_calls']),
                    'successful_calls': int(result['successful_calls']),
                    'avg_latency': float(result['avg_latency']) if result['avg_latency'] is not None else 1000.0,
                    'success_rate': float(result['success_rate']) if result['success_rate'] is not None else 1.0
                }
            else:
                # Return default values for new providers
                return {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'avg_latency': 1000.0,
                    'success_rate': 1.0
                }
                
        except Exception as e:
            logger.error(f"Error getting provider performance: {e}")
            return {'success_rate': 1.0, 'avg_latency': 1000, 'total_calls': 0}
    
    def select_best_provider(self) -> Optional[str]:
        """
        Select best available provider based on:
        1. Quota availability
        2. Recent success rate
        3. Performance (latency)
        4. Priority
        
        Returns:
            Name of best provider or None if all exhausted
        """
        candidates = []
        
        for name, config in self.providers.items():
            # Check quota
            usage = self.get_quota_usage_today(name)
            quota_remaining = config['daily_limit'] - usage
            
            if quota_remaining <= 0:
                logger.warning(f"{name} quota exhausted: {usage}/{config['daily_limit']}")
                continue
            
            # Get performance
            perf = self.get_provider_performance(name, hours=1)
            
            # Calculate score (higher is better)
            quota_score = (quota_remaining / config['daily_limit']) * 100
            success_score = perf['success_rate'] * 50
            speed_score = (1000 / max(perf['avg_latency'], 1)) * 30
            priority_score = (10 / config['priority']) * 20
            
            total_score = quota_score + success_score + speed_score + priority_score
            
            candidates.append({
                'name': name,
                'score': total_score,
                'quota_remaining': quota_remaining,
                'quota_percentage': (quota_remaining / config['daily_limit']) * 100,
                'success_rate': perf['success_rate'],
                'avg_latency': perf['avg_latency'],
                'priority': config['priority']
            })
        
        if not candidates:
            logger.error("No providers available! All quotas exhausted.")
            return None
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        
        logger.info(
            f"Selected: {best['name']} | "
            f"Score: {best['score']:.1f} | "
            f"Quota: {best['quota_remaining']} ({best['quota_percentage']:.1f}%) | "
            f"Success: {best['success_rate']:.1%} | "
            f"Latency: {best['avg_latency']:.0f}ms"
        )
        
        return best['name']
    
    def record_api_call(self, provider_name: str, success: bool, 
                       latency_ms: int, error_message: Optional[str] = None,
                       quota_remaining: Optional[int] = None):
        """
        Record API call result for learning and tracking
        
        Args:
            provider_name: Name of the provider
            success: Whether the call succeeded
            latency_ms: Response latency in milliseconds
            error_message: Error message if failed
            quota_remaining: Remaining quota (if available)
        """
        try:
            cursor = self.db_conn.cursor()
            
            # Record performance
            cursor.execute("""
                INSERT INTO provider_performance
                (provider_name, success, latency_ms, error_message, quota_remaining, daily_quota)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                provider_name, 
                success, 
                latency_ms, 
                error_message,
                quota_remaining,
                self.providers[provider_name]['daily_limit'] if provider_name in self.providers else None
            ))
            
            # Update daily quota
            cursor.execute("""
                INSERT INTO daily_quota_usage 
                (date, provider_name, calls_made, calls_successful, quota_limit)
                VALUES (CURRENT_DATE, %s, 1, %s, %s)
                ON CONFLICT (date, provider_name) 
                DO UPDATE SET
                    calls_made = daily_quota_usage.calls_made + 1,
                    calls_successful = daily_quota_usage.calls_successful + %s,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                provider_name, 
                1 if success else 0,
                self.providers[provider_name]['daily_limit'] if provider_name in self.providers else 0,
                1 if success else 0
            ))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error recording API call: {e}")
            self.db_conn.rollback()
    
    def make_api_call(self, provider_name: str, prompt: str) -> Dict:
        """
        Make API call to specified provider
        
        Args:
            provider_name: Name of the provider
            prompt: Prompt text
            
        Returns:
            Result dictionary with success, content, latency, etc.
        """
        if provider_name not in self.providers:
            return {
                'success': False,
                'error': f"Provider {provider_name} not configured",
                'latency_ms': 0,
                'provider': provider_name
            }
        
        provider = self.providers[provider_name]
        start_time = datetime.now()
        
        try:
            if provider['type'] == 'openai_compatible':
                # OpenAI-compatible API (Groq, Together, OpenAI)
                response = requests.post(
                    provider['endpoint'],
                    headers={
                        'Authorization': f"Bearer {provider['api_key']}",
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': provider['model'],
                        'messages': [
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.3,
                        'max_tokens': 500
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                result = response.json()
                
                self.record_api_call(provider_name, True, latency)
                
                return {
                    'success': True,
                    'content': result['choices'][0]['message']['content'],
                    'latency_ms': latency,
                    'provider': provider_name
                }
            
            elif provider['type'] == 'gemini':
                # Gemini API
                response = requests.post(
                    f"{provider['endpoint']}?key={provider['api_key']}",
                    headers={'Content-Type': 'application/json'},
                    json={
                        'contents': [{'parts': [{'text': prompt}]}],
                        'generationConfig': {
                            'temperature': 0.3,
                            'maxOutputTokens': 500
                        }
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                result = response.json()
                
                self.record_api_call(provider_name, True, latency)
                
                return {
                    'success': True,
                    'content': result['candidates'][0]['content']['parts'][0]['text'],
                    'latency_ms': latency,
                    'provider': provider_name
                }
        
        except requests.exceptions.Timeout:
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = "Request timeout"
            self.record_api_call(provider_name, False, latency, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'latency_ms': latency,
                'provider': provider_name
            }
            
        except requests.exceptions.HTTPError as e:
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            self.record_api_call(provider_name, False, latency, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'latency_ms': latency,
                'provider': provider_name
            }
            
        except Exception as e:
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = str(e)[:200]
            self.record_api_call(provider_name, False, latency, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'latency_ms': latency,
                'provider': provider_name
            }


class LLMClient:
    """
    Unified LLM client with intelligent provider routing
    """
    
    def __init__(self, db_conn):
        """
        Initialize LLM client
        
        Args:
            db_conn: PostgreSQL database connection
        """
        self.provider_manager = ProviderManager(db_conn)
        logger.info("LLMClient initialized")
    
    def classify(self, email_text: str) -> Dict:
        """
        Classify email using best available provider
        
        Args:
            email_text: Combined email subject and body
            
        Returns:
            Classification result dictionary
        """
        prompt = f"""You are a job application email classifier. Classify this email into ONE of these categories:

CATEGORIES:
1. INTERVIEW - Email inviting candidate for interview, phone screen, technical round, or any meeting
   Examples: "We'd like to schedule an interview", "Next steps in our hiring process", "Invite you to meet"

2. REJECTION - Email declining or rejecting the application  
   Examples: "We've decided to move forward with other candidates", "Unfortunately", "Not moving forward",
   "We regret to inform", "Not selected", "Position has been filled", "Not the right fit"

3. OFFER - Email extending a job offer, discussing compensation, or congratulating on selection
   Examples: "Pleased to offer you the position", "Offer letter attached", "Welcome to the team"

4. OTHER - Application received confirmation, general updates, or non-job emails
   Examples: "Application received", "Thank you for applying", spam, marketing emails

CRITICAL RULES FOR REJECTION:
- Look for phrases like: "not moving forward", "other candidates", "decided to pursue", "unfortunately", 
  "not selected", "regret to inform", "position filled", "not the right fit", "declined", "unsuccessful"
- Even if polite or thanking the candidate, if they're being turned down → REJECTION
- "We'll keep your resume on file" usually means REJECTION

ANTI-SPAM RULES:
- Credit card offers, loans, banking → OTHER
- Marketing emails → OTHER
- Only real recruiting emails → INTERVIEW/OFFER/REJECTION

Email to classify:
{email_text[:1000]}

Respond ONLY in this format:
CLASSIFICATION: <INTERVIEW|REJECTION|OFFER|OTHER>
CONFIDENCE: <0.0-1.0>"""
        
        # Try providers until one succeeds
        max_attempts = 3
        rate_limit_detected = False
        last_error = ""

        for attempt in range(max_attempts):
            provider_name = self.provider_manager.select_best_provider()
            
            if not provider_name:
                logger.error("No providers available!")
                raise Exception("All API quotas exhausted")
            
            logger.info(f"Attempt {attempt + 1}/{max_attempts}: Trying {provider_name}")
            result = self.provider_manager.make_api_call(provider_name, prompt)
            
            if result['success']:
                # Parse response
                classification = self.parse_classification(result['content'])
                classification['provider'] = provider_name
                classification['latency_ms'] = result['latency_ms']
                classification['method'] = 'ai'
                
                logger.info(
                    f"✓ Classified with {provider_name}: "
                    f"{classification['classification']} "
                    f"(confidence: {classification['confidence']:.2f}, "
                    f"latency: {result['latency_ms']}ms)"
                )
                
                return classification
            else:
                error_msg = result.get('error', 'Unknown error')
                last_error = error_msg
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    rate_limit_detected = True
                logger.warning(f"✗ {provider_name} failed: {error_msg}")
                continue
        
        if rate_limit_detected and last_error:
            raise Exception(f"Rate limit: {last_error}")
        if last_error:
            raise Exception(last_error)
        
        raise Exception(f"All {max_attempts} classification attempts failed")
    
    def parse_classification(self, response_text: str) -> Dict:
        """
        Parse LLM response
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed classification dictionary
        """
        import re
        
        classification_match = re.search(r'CLASSIFICATION:\s*(\w+)', response_text, re.IGNORECASE)
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response_text, re.IGNORECASE)
        
        classification = classification_match.group(1).upper() if classification_match else 'OTHER'
        confidence = float(confidence_match.group(1)) if confidence_match else 0.8
        
        # Validate classification
        valid_classifications = ['INTERVIEW', 'REJECTION', 'OFFER', 'OTHER']
        if classification not in valid_classifications:
            logger.warning(f"Invalid classification '{classification}', defaulting to OTHER")
            classification = 'OTHER'
        
        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            'classification': classification,
            'confidence': confidence
        }
