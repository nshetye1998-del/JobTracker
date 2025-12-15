"""
Company Name Extractor
Intelligently extracts company names from email subject, body, and sender
"""

import re
from typing import Optional, Tuple
from libs.core.logger import configure_logger

logger = configure_logger("company_extractor")

# Known companies by domain
KNOWN_COMPANIES = {
    'google.com': 'Google',
    'meta.com': 'Meta',
    'facebook.com': 'Meta',
    'amazon.com': 'Amazon',
    'amazon.jobs': 'Amazon',
    'microsoft.com': 'Microsoft',
    'apple.com': 'Apple',
    'netflix.com': 'Netflix',
    'tesla.com': 'Tesla',
    'uber.com': 'Uber',
    'lyft.com': 'Lyft',
    'airbnb.com': 'Airbnb',
    'stripe.com': 'Stripe',
    'spotify.com': 'Spotify',
    'snap.com': 'Snap',
    'twitter.com': 'Twitter',
    'salesforce.com': 'Salesforce',
    'oracle.com': 'Oracle',
    'nvidia.com': 'NVIDIA',
    'intel.com': 'Intel',
    'ibm.com': 'IBM',
    'adobe.com': 'Adobe',
    'paypal.com': 'PayPal',
    'shopify.com': 'Shopify',
    'zoom.us': 'Zoom',
    'slack.com': 'Slack',
    'dropbox.com': 'Dropbox',
    'atlassian.com': 'Atlassian',
    'github.com': 'GitHub',
    'gitlab.com': 'GitLab',
    'reddit.com': 'Reddit',
    'pinterest.com': 'Pinterest',
    'discord.com': 'Discord',
    'roblox.com': 'Roblox',
    'databricks.com': 'Databricks',
    'snowflake.com': 'Snowflake',
    'mongodb.com': 'MongoDB',
    'coinbase.com': 'Coinbase',
    'robinhood.com': 'Robinhood',
    'doordash.com': 'DoorDash',
    'instacart.com': 'Instacart',
    'waymo.com': 'Waymo',
    'openai.com': 'OpenAI',
    'anthropic.com': 'Anthropic',
}

# Domains to ignore (job boards, email services)
IGNORE_DOMAINS = {
    'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
    'greenhouse.io', 'lever.co', 'workday.com', 'taleo.net',
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
    'icims.com', 'myworkdayjobs.com', 'bamboohr.com'
}

# Suffixes to remove
COMPANY_SUFFIXES = [
    'Inc.', 'Inc', 'LLC', 'L.L.C.', 'Corp.', 'Corp', 'Corporation',
    'Limited', 'Ltd.', 'Ltd', 'Co.', 'Co', 'Company', 'Group',
    'Technologies', 'Technology', 'Tech', 'Systems', 'Solutions',
    'Enterprises', 'Holdings', 'Partners', 'Team', 'Recruiting',
    'Careers', 'Talent', 'Hiring'
]


class CompanyExtractor:
    """Extract company names from emails using multiple strategies"""
    
    def __init__(self):
        self.logger = logger
    
    def extract(self, subject: str = "", body: str = "", from_email: str = "") -> str:
        """
        Extract company name from email using multiple strategies
        
        Priority:
        1. Known domain mapping
        2. Subject line patterns
        3. Body patterns
        4. Domain name (if not in ignore list)
        
        Returns:
            Company name or "Unknown"
        """
        # Strategy 1: Check for known company domain
        company = self._extract_from_domain(from_email)
        if company and company != "Unknown":
            self.logger.debug(f"Found company from domain: {company}")
            return company
        
        # Strategy 2: Extract from subject line (most reliable)
        company = self._extract_from_subject(subject)
        if company and company != "Unknown":
            self.logger.debug(f"Found company from subject: {company}")
            return company
        
        # Strategy 3: Extract from body
        company = self._extract_from_body(body[:500])  # First 500 chars
        if company and company != "Unknown":
            self.logger.debug(f"Found company from body: {company}")
            return company
        
        # Strategy 4: Try to infer from domain (if not a job board)
        company = self._infer_from_domain(from_email)
        if company and company != "Unknown":
            self.logger.debug(f"Inferred company from domain: {company}")
            return company
        
        self.logger.debug("Could not extract company name")
        return "Unknown"
    
    def _extract_from_domain(self, email: str) -> Optional[str]:
        """Extract from known company domains"""
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower()
            
            # Check exact match
            if domain in KNOWN_COMPANIES:
                return KNOWN_COMPANIES[domain]
            
            # Check if it's a subdomain of known company
            for known_domain, company_name in KNOWN_COMPANIES.items():
                if domain.endswith(known_domain):
                    return company_name
        except (IndexError, AttributeError):
            pass
        
        return None
    
    def _extract_from_subject(self, subject: str) -> Optional[str]:
        """Extract company name from subject line"""
        if not subject:
            return None
        
        # Remove common email prefixes (Re:, Fwd:, etc.)
        subject_clean = re.sub(r'^(?:Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE).strip()
        
        # Pattern 1: "Interview at Google" or "Interview with Google"
        match = re.search(r'\b(?:at|with|for|from)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s*[-–—:]|\s*$)', subject_clean)
        if match:
            company = self._clean_company_name(match.group(1))
            if self._is_valid_company(company):
                return company
        
        # Pattern 2: "Google - Software Engineer" or "Google: Software Engineer"
        # Skip if starts with common words like "Senior", "Application", etc.
        match = re.search(r'^([A-Z][A-Za-z0-9\s&]+?)\s*[-–—:]', subject_clean)
        if match:
            company = self._clean_company_name(match.group(1))
            # Validate it's not a job title or generic word
            company_lower = company.lower()
            invalid_phrases = ['senior', 'application', 'position', 'job', 'interview', 'offer', 
                             'interview invitation', 'job alert', 'new job', 'application status',
                             'your application', 'invitation to']
            if self._is_valid_company(company) and not any(phrase in company_lower for phrase in invalid_phrases):
                return company
        
        # Pattern 3: "[Company Name]" or "(Company Name)"
        match = re.search(r'[\[\(]([A-Z][A-Za-z0-9\s&]+?)[\]\)]', subject_clean)
        if match:
            company = self._clean_company_name(match.group(1))
            if self._is_valid_company(company):
                return company
        
        # Pattern 4: "Company Name Team" or "Company Name Careers"
        match = re.search(r'([A-Z][A-Za-z0-9\s&]+?)\s+(?:Team|Careers|Recruiting|Talent|Hiring)', subject_clean, re.IGNORECASE)
        if match:
            company = self._clean_company_name(match.group(1))
            if self._is_valid_company(company):
                return company
        
        return None
    
    def _extract_from_body(self, body: str) -> Optional[str]:
        """Extract company name from email body"""
        if not body:
            return None
        
        # Pattern 1: "at Company Name" or "with Company Name"
        match = re.search(r'\b(?:at|with|for|from)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:Inc|LLC|Corp)|[,.\n])', body)
        if match:
            company = self._clean_company_name(match.group(1))
            if self._is_valid_company(company):
                return company
        
        # Pattern 2: "Company Name is" or "Company Name has"
        match = re.search(r'([A-Z][A-Za-z0-9\s&]{3,30}?)\s+(?:is|has|invites|would like)', body)
        if match:
            company = self._clean_company_name(match.group(1))
            if self._is_valid_company(company):
                return company
        
        return None
    
    def _infer_from_domain(self, email: str) -> Optional[str]:
        """Infer company name from domain if not in ignore list"""
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower()
            
            # Skip if it's an ignored domain
            if any(ignored in domain for ignored in IGNORE_DOMAINS):
                return None
            
            # Extract the main part of the domain
            parts = domain.split('.')
            if len(parts) >= 2:
                company_part = parts[-2]  # e.g., "uber" from "careers.uber.com"
                
                # Capitalize properly
                company = company_part.capitalize()
                
                # Only return if it looks like a real company name (not too short)
                if len(company) >= 3:
                    return company
        except (IndexError, AttributeError):
            pass
        
        return None
    
    def _clean_company_name(self, name: str) -> str:
        """Clean company name by removing common suffixes"""
        if not name:
            return name
        
        cleaned = name.strip()
        
        # Remove common suffixes
        for suffix in COMPANY_SUFFIXES:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Remove trailing punctuation
        cleaned = cleaned.rstrip('.,;:!?')
        
        return cleaned.strip()
    
    def _is_valid_company(self, name: str) -> bool:
        """Check if extracted name looks like a valid company"""
        if not name or len(name) < 2:
            return False
        
        # Should start with capital letter
        if not name[0].isupper():
            return False
        
        # Should not be too long (likely extracted wrong)
        if len(name) > 50:
            return False
        
        # Should not be common non-company words
        invalid_words = {'Your', 'The', 'This', 'We', 'Our', 'You', 'Please', 'Thank', 'Dear', 'Hi', 'Hello'}
        if name in invalid_words:
            return False
        
        return True
