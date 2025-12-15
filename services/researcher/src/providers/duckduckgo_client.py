"""
DuckDuckGo Search Provider
No API key needed, unlimited (with rate limiting)
"""

from duckduckgo_search import DDGS
from .base_provider import BaseResearchProvider
from typing import List, Dict
from loguru import logger


class DuckDuckGoClient(BaseResearchProvider):
    """DuckDuckGo search provider (no API key needed, unlimited)"""
    
    def __init__(self):
        super().__init__()
        self.client = DDGS()
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            results_raw = self.client.text(query, max_results=max_results)
            
            results = []
            for item in results_raw:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", "")
                })
            
            logger.info(f"✅ DuckDuckGo: Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ DuckDuckGo error: {e}")
            raise
