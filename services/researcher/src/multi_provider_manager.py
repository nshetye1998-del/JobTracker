"""
Multi-Provider Research Manager
Manages multiple research providers with intelligent failover and rate limiting
"""

import os
from typing import Dict, Optional
from loguru import logger
from rate_limiter import ProviderRateLimiter
from providers import TavilyClient, GoogleClient, SerpAPIClient, DuckDuckGoClient


class MultiProviderResearchManager:
    """Manages multiple research providers with intelligent failover"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.rate_limiter = ProviderRateLimiter(db_connection)
        self.providers = self._initialize_providers()
        
        logger.info(f"✅ Initialized {len(self.providers)} research providers")
    
    def _initialize_providers(self) -> Dict:
        """Initialize all available providers"""
        providers = {}
        
        # Tavily
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            providers["tavily"] = TavilyClient(tavily_key)
            logger.info("✅ Tavily provider ready")
        else:
            logger.warning("⚠️  Tavily API key not found")
        
        # Google Custom Search
        google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        google_cx = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_CX")
        if google_key and google_cx:
            providers["google"] = GoogleClient(google_key, google_cx)
            logger.info("✅ Google provider ready")
        else:
            logger.warning("⚠️  Google Custom Search credentials not found")
        
        # SerpAPI
        serpapi_key = os.getenv("SERPAPI_KEY")
        if serpapi_key:
            providers["serpapi"] = SerpAPIClient(serpapi_key)
            logger.info("✅ SerpAPI provider ready")
        else:
            logger.warning("⚠️  SerpAPI key not found")
        
        # DuckDuckGo (no key needed)
        try:
            providers["duckduckgo"] = DuckDuckGoClient()
            logger.info("✅ DuckDuckGo provider ready")
        except Exception as e:
            logger.warning(f"⚠️  DuckDuckGo unavailable: {e}")
        
        return providers
    
    def research_company(self, company_name: str, role: str = None) -> Dict:
        """
        Research a company using first available provider
        Auto-failover if provider fails or is rate limited
        OPTIMIZED: Only try each provider once for fast failover
        """
        
        # Try each provider once - no retries for speed
        # This allows quick failover to fallback research
        tried_providers = set()
        max_attempts = len(self.providers)
        
        while len(tried_providers) < max_attempts:
            # Get next available provider
            provider_name = self.rate_limiter.get_next_available_provider()
            
            if not provider_name or provider_name in tried_providers:
                logger.error("❌ All providers exhausted or rate limited!")
                return {
                    "success": False,
                    "error": "All providers rate limited",
                    "company_info": None
                }
            
            tried_providers.add(provider_name)
            
            # Get provider client
            provider = self.providers.get(provider_name)
            if not provider:
                logger.error(f"❌ Provider {provider_name} not initialized")
                continue
            
            # Attempt research
            logger.info(f"🔍 Researching '{company_name}' using {provider_name}...")
            result = provider.research_company(company_name, role)
            
            # Record usage
            self.rate_limiter.record_request(
                provider_name=provider_name,
                success=result["success"],
                response_time_ms=result.get("response_time_ms"),
                error_message=result.get("error")
            )
            
            if result["success"]:
                logger.info(f"✅ Research complete via {provider_name}")
                return result
            else:
                logger.warning(f"⚠️  {provider_name} failed: {result.get('error')}")
                # Move to next provider immediately without retry
        
        # All providers failed
        return {
            "success": False,
            "error": "All providers failed",
            "company_info": None
        }
    
    def get_provider_stats(self) -> Dict:
        """Get statistics for all providers"""
        return self.rate_limiter.get_provider_stats()
