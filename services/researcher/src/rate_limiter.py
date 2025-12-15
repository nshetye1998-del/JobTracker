"""
Rate Limiter for Multi-Provider Research System
Tracks and enforces per-provider rate limits using PostgreSQL
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger


class ProviderRateLimiter:
    """Track and enforce rate limits for each research provider"""
    
    # Provider limits (requests per day and cooldown in seconds)
    PROVIDER_LIMITS = {
        "tavily": {
            "requests_per_day": 33,      # 1000/month ÷ 30 days
            "cooldown": 45,              # 45 seconds between calls (safe margin)
            "priority": 1                # Higher priority = use first
        },
        "google": {
            "requests_per_day": 100,     # 100/day free tier
            "cooldown": 10,              # 10 seconds between calls
            "priority": 2                # Use after Tavily
        },
        "serpapi": {
            "requests_per_day": 3,       # 100/month ÷ 30 days
            "cooldown": 300,             # 5 minutes (very limited)
            "priority": 4                # Use as last resort
        },
        "duckduckgo": {
            "requests_per_day": 500,     # Conservative limit (no official limit)
            "cooldown": 5,               # 5 seconds between calls
            "priority": 3                # Use before SerpAPI
        }
    }
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create provider_usage table if not exists"""
        cursor = self.db.cursor()
        
        query = """
        CREATE TABLE IF NOT EXISTS provider_usage (
            id SERIAL PRIMARY KEY,
            provider_name VARCHAR(50) NOT NULL,
            request_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            success BOOLEAN DEFAULT true,
            response_time_ms INTEGER,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_provider_timestamp 
        ON provider_usage(provider_name, request_timestamp DESC);
        """
        
        cursor.execute(query)
        self.db.commit()
        cursor.close()
        
        logger.info("✅ Provider usage tracking table ready")
    
    def can_use_provider(self, provider_name: str) -> bool:
        """Check if provider is available (not rate limited or consistently failing)"""
        
        if provider_name not in self.PROVIDER_LIMITS:
            logger.error(f"❌ Unknown provider: {provider_name}")
            return False
        
        limits = self.PROVIDER_LIMITS[provider_name]
        
        # Check daily limit - if exhausted, skip immediately without cooldown check
        daily_count = self._get_daily_request_count(provider_name)
        if daily_count >= limits["requests_per_day"]:
            logger.warning(f"⏸️  {provider_name}: Daily limit reached ({daily_count}/{limits['requests_per_day']})")
            return False
        
        # Check if provider has recent consecutive failures (indicates API issues)
        # If last 3 attempts failed, skip this provider to avoid wasting time
        recent_failures = self._get_recent_failure_count(provider_name, limit=3)
        if recent_failures >= 3:
            logger.warning(f"⏸️  {provider_name}: {recent_failures} consecutive failures, skipping")
            return False
        
        return True
    
    def _get_daily_request_count(self, provider_name: str) -> int:
        """Get number of requests made today for this provider"""
        cursor = self.db.cursor()
        
        query = """
        SELECT COUNT(*) 
        FROM provider_usage 
        WHERE provider_name = %s 
          AND request_timestamp > NOW() - INTERVAL '24 hours'
          AND success = true
        """
        
        cursor.execute(query, (provider_name,))
        result = cursor.fetchone()
    
    def _get_recent_failure_count(self, provider_name: str, limit: int = 3) -> int:
        """Get number of consecutive recent failures for this provider"""
        cursor = self.db.cursor()
        
        query = """
        SELECT success 
        FROM provider_usage 
        WHERE provider_name = %s 
        ORDER BY request_timestamp DESC 
        LIMIT %s
        """
        
        cursor.execute(query, (provider_name, limit))
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            return 0
        
        # Count consecutive failures from most recent
        consecutive_failures = 0
        for (success,) in results:
            if not success:
                consecutive_failures += 1
            else:
                break
        
        return consecutive_failures
        cursor.close()
        
        return result[0] if result else 0
    
    def _get_last_request_time(self, provider_name: str) -> Optional[datetime]:
        """Get timestamp of last request for this provider"""
        cursor = self.db.cursor()
        
        query = """
        SELECT request_timestamp 
        FROM provider_usage 
        WHERE provider_name = %s 
        ORDER BY request_timestamp DESC 
        LIMIT 1
        """
        
        cursor.execute(query, (provider_name,))
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else None
    
    def record_request(self, provider_name: str, success: bool, 
                      response_time_ms: int = None, error_message: str = None):
        """Record a request for tracking and rate limiting"""
        cursor = self.db.cursor()
        
        query = """
        INSERT INTO provider_usage 
        (provider_name, request_timestamp, success, response_time_ms, error_message)
        VALUES (%s, NOW(), %s, %s, %s)
        """
        
        cursor.execute(query, (provider_name, success, response_time_ms, error_message))
        self.db.commit()
        cursor.close()
        
        if success:
            daily_count = self._get_daily_request_count(provider_name)
            limit = self.PROVIDER_LIMITS[provider_name]["requests_per_day"]
            logger.info(f"📊 {provider_name}: {daily_count}/{limit} requests today")
    
    def get_next_available_provider(self) -> Optional[str]:
        """Get the next available provider based on priority and rate limits"""
        
        # Sort providers by priority (lower number = higher priority)
        sorted_providers = sorted(
            self.PROVIDER_LIMITS.items(),
            key=lambda x: x[1]["priority"]
        )
        
        for provider_name, limits in sorted_providers:
            if self.can_use_provider(provider_name):
                logger.info(f"✅ Selected provider: {provider_name}")
                return provider_name
        
        # All providers rate limited
        logger.warning("⚠️  All providers rate limited! Need to wait.")
        return None
    
    def get_provider_stats(self) -> Dict:
        """Get usage statistics for all providers"""
        stats = {}
        
        for provider_name in self.PROVIDER_LIMITS.keys():
            daily_count = self._get_daily_request_count(provider_name)
            limit = self.PROVIDER_LIMITS[provider_name]["requests_per_day"]
            last_request = self._get_last_request_time(provider_name)
            
            stats[provider_name] = {
                "daily_usage": daily_count,
                "daily_limit": limit,
                "remaining": limit - daily_count,
                "last_request": last_request.isoformat() if last_request else None,
                "available": self.can_use_provider(provider_name)
            }
        
        return stats
