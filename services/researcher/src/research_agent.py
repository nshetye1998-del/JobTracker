import json
import time
from datetime import datetime
from typing import Optional
import redis
from tavily import TavilyClient
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger
from libs.core.llm_client import LLMClient

logger = configure_logger("research_agent")

class ResearchConfig(BaseConfig):
    SERVICE_NAME: str = "researcher"
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "auto"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CACHE_TTL_DAYS: int = 7

config = get_config(ResearchConfig)

class ResearchAgent:
    def __init__(self):
        if not config.TAVILY_API_KEY:
            logger.error("TAVILY_API_KEY is required")
            raise ValueError("TAVILY_API_KEY is required")
            
        self.tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        self.llm = LLMClient()
        
        # Initialize Redis for caching
        try:
            self.redis = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis.ping()
            logger.info(f"✓ Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis = None
        
        # Cache TTL: 7 days (in seconds)
        self.cache_ttl = config.CACHE_TTL_DAYS * 24 * 3600
        
        logger.info("Research Agent initialized with LLMClient + Tavily + Redis caching.")

    def get_cache_key(self, company: str) -> str:
        """Generate cache key for research data"""
        return f"research:{company.lower()}"
    
    def get_cached_research(self, company: str) -> Optional[str]:
        """Check if research data is cached"""
        if not self.redis:
            return None
        
        try:
            cache_key = self.get_cache_key(company)
            cached = self.redis.get(cache_key)
            
            if cached:
                data = json.loads(cached)
                cached_at = datetime.fromisoformat(data['cached_at'])
                age_days = (datetime.utcnow() - cached_at).days
                
                logger.info(f"✅ CACHE HIT for {company} (age: {age_days} days)")
                return data['briefing']
            
            logger.info(f"❌ CACHE MISS for {company}")
            return None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def cache_research(self, company: str, briefing: str):
        """Cache research data for 7 days"""
        if not self.redis:
            return
        
        try:
            cache_key = self.get_cache_key(company)
            data = {
                'briefing': briefing,
                'cached_at': datetime.utcnow().isoformat(),
                'company': company
            }
            
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
            logger.info(f"💾 Cached research for {company} (TTL: {config.CACHE_TTL_DAYS} days)")
        except Exception as e:
            logger.error(f"Cache write error: {e}")

    def research_company(self, company_name: str) -> str:
        logger.info(f"Researching company: {company_name}...")
        
        # Check cache first
        cached_briefing = self.get_cached_research(company_name)
        if cached_briefing:
            return cached_briefing
        
        # Cache miss - perform research
        logger.info(f"Performing fresh research for {company_name}...")
        research_start = time.time()
        
        # 1. Search Tavily
        try:
            search_result = self.tavily.search(
                query=f"{company_name} recent news mission interview process",
                search_depth="advanced",
                max_results=5
            )
            context = "\n".join([r['content'] for r in search_result['results']])
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return "Research failed due to search error."

        # 2. Synthesize with LLM
        prompt = f"""You are a career intelligence analyst. 
Based on the following search results, write a 3-paragraph briefing about {company_name}.
Include:
1. Company Mission/What they do
2. Recent News/Developments
3. Interview Process/Culture (if available)

Search Results:
{context}

Return ONLY the briefing text.
"""
        try:
            briefing = self.llm.generate_text(prompt)
            research_duration = time.time() - research_start
            logger.info(f"Research completed in {research_duration:.2f}s")
            
            # Cache the result
            self.cache_research(company_name, briefing)
            
            return briefing
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return "Research failed due to LLM error."
