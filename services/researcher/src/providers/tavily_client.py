"""
Tavily Research Provider
1000 requests/month free tier
"""

from tavily import TavilyClient as Tavily
from .base_provider import BaseResearchProvider
from typing import List, Dict
from loguru import logger


class TavilyClient(BaseResearchProvider):
    """Tavily search provider (1000 requests/month)"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = Tavily(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using Tavily API"""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"
            )
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")
                })
            
            logger.info(f"✅ Tavily: Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Tavily error: {e}")
            raise
