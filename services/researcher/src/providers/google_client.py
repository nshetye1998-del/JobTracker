"""
Google Custom Search Provider
100 requests/day free tier
"""

import requests
from .base_provider import BaseResearchProvider
from typing import List, Dict
from loguru import logger


class GoogleClient(BaseResearchProvider):
    """Google Custom Search provider (100 requests/day)"""
    
    def __init__(self, api_key: str, cx: str):
        super().__init__(api_key)
        self.cx = cx
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using Google Custom Search API"""
        try:
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": min(max_results, 10)  # Google max is 10
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            logger.info(f"✅ Google: Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Google error: {e}")
            raise
