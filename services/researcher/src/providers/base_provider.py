"""
Base Provider Class
Abstract class for all research providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import time


class BaseResearchProvider(ABC):
    """Base class for all research providers"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.name = self.__class__.__name__.replace('Client', '').lower()
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for information about a company
        Returns list of results with: title, url, snippet
        """
        pass
    
    def research_company(self, company_name: str, role: str = None) -> Dict:
        """
        Research a company for job application
        Returns: company_info, salary_range, industry, size, etc.
        """
        start_time = time.time()
        
        try:
            # Build search query
            query = self._build_search_query(company_name, role)
            
            # Execute search
            results = self.search(query, max_results=5)
            
            # Extract information
            company_info = self._extract_company_info(results, company_name)
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "provider": self.name,
                "company_info": company_info,
                "response_time_ms": response_time,
                "sources": results[:5]  # Return full result objects with title, url, snippet
            }
        
        except Exception as e:
            return {
                "success": False,
                "provider": self.name,
                "error": str(e),
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def _build_search_query(self, company_name: str, role: str = None) -> str:
        """Build optimized search query"""
        if role:
            return f"{company_name} {role} salary range glassdoor"
        return f"{company_name} company overview careers"
    
    def _extract_company_info(self, results: List[Dict], company_name: str) -> Dict:
        """Extract structured info from search results"""
        # Combine all snippets
        combined_text = " ".join([r.get("snippet", "") for r in results])
        
        return {
            "company": company_name,
            "description": combined_text[:500],  # First 500 chars
            "sources_count": len(results)
        }
