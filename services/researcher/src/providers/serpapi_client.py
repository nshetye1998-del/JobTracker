"""
SerpAPI Provider
100 requests/month free tier
"""

import requests
from .base_provider import BaseResearchProvider
from typing import List, Dict
from loguru import logger


class SerpAPIClient(BaseResearchProvider):
    """SerpAPI provider (100 requests/month)"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://serpapi.com/search"
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using SerpAPI"""
        try:
            params = {
                "api_key": self.api_key,
                "q": query,
                "num": max_results,
                "engine": "google"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            logger.info(f"✅ SerpAPI: Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ SerpAPI error: {e}")
            raise
