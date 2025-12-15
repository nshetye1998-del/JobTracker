"""
Role Extractor: Extract job role/title from email subject and body

Intelligently extracts the job role from email content using:
1. Common role title patterns
2. Keyword-based extraction
3. Subject line parsing
"""

import re
from typing import Optional
from libs.core.logger import configure_logger

logger = configure_logger("role_extractor")


class RoleExtractor:
    """Extract job role/title from email content"""
    
    # Common role keywords that indicate job titles
    ROLE_KEYWORDS = {
        # Engineering
        'software engineer', 'swe', 'backend engineer', 'frontend engineer', 
        'full stack engineer', 'fullstack engineer', 'devops engineer',
        'site reliability engineer', 'sre', 'platform engineer',
        'mobile engineer', 'ios engineer', 'android engineer',
        'machine learning engineer', 'ml engineer', 'data engineer',
        'security engineer', 'infrastructure engineer',
        
        # Data Science
        'data scientist', 'research scientist', 'applied scientist',
        'data analyst', 'business analyst', 'analytics engineer',
        
        # Management
        'engineering manager', 'technical lead', 'tech lead', 'tl',
        'staff engineer', 'principal engineer', 'senior engineer',
        'lead engineer', 'architect', 'solutions architect',
        
        # Product
        'product manager', 'pm', 'tpm', 'technical program manager',
        'product designer', 'ux designer', 'ui designer',
        
        # Other
        'developer', 'programmer', 'consultant', 'specialist',
        'researcher', 'intern', 'internship'
    }
    
    def __init__(self):
        """Initialize the role extractor"""
        self.logger = logger
    
    def extract(self, subject: str, body: str) -> str:
        """
        Extract role from email subject and body
        
        Args:
            subject: Email subject line
            body: Email body/snippet
            
        Returns:
            Extracted role title or "General" if not found
        """
        # Combine subject and body for analysis
        text = f"{subject} {body}".lower()
        
        # Strategy 1: Look for explicit patterns in subject
        role = self._extract_from_subject(subject)
        if role:
            return self._clean_role(role)
        
        # Strategy 2: Look for role keywords in text
        role = self._extract_from_keywords(text)
        if role:
            return self._clean_role(role)
        
        # Strategy 3: Pattern matching for common formats
        role = self._extract_from_patterns(text)
        if role:
            return self._clean_role(role)
        
        # Default fallback
        return "General"
    
    def _extract_from_subject(self, subject: str) -> Optional[str]:
        """Extract role from subject line patterns"""
        if not subject:
            return None
        
        # Common subject patterns:
        # "Interview for Software Engineer"
        # "Google - Software Engineer Interview"
        # "Software Engineer at Meta"
        # "Your application for Senior SWE"
        # "Re: Senior Backend Engineer Position"
        
        patterns = [
            r'(?:for|as)\s+(?:a\s+)?([^-\n]+?)(?:\s+at|\s+position|\s+role|$)',
            r'-\s*([^-\n]+?)\s+(?:interview|offer|position|role)',
            r'(?:interview|offer|position|role).*?(?:for|as)\s+([^-\n]+?)(?:\s+at|$)',
            r'^([^-:]+?)\s+(?:interview|offer|position|role)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                if len(role) > 5 and len(role) < 80:  # Reasonable length
                    return role
        
        return None
    
    def _extract_from_keywords(self, text: str) -> Optional[str]:
        """Find role using keyword matching"""
        # Look for known role keywords
        for role_keyword in self.ROLE_KEYWORDS:
            if role_keyword in text:
                # Try to get context around the keyword
                # Example: "Software Engineer II" or "Senior Software Engineer"
                pattern = rf'\b((?:senior|staff|principal|lead|junior|associate)?\s*{re.escape(role_keyword)}\s*(?:i{1,3}|iv|v|[1-5])?)\b'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
                else:
                    return role_keyword
        
        return None
    
    def _extract_from_patterns(self, text: str) -> Optional[str]:
        """Extract using common text patterns"""
        # Pattern: "the [role] position"
        match = re.search(r'the\s+([^.,:;]+?)\s+(?:position|role|opening)', text, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            if len(role) > 5 and len(role) < 80:
                return role
        
        # Pattern: "apply for [role]" or "applied for [role]"
        match = re.search(r'appl(?:y|ied)\s+for\s+(?:the\s+)?([^.,:;]+?)(?:\s+at|\s+with|$)', text, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            if len(role) > 5 and len(role) < 80:
                return role
        
        return None
    
    def _clean_role(self, role: str) -> str:
        """Clean and normalize the extracted role"""
        # Remove common noise words
        noise_words = [
            'position', 'role', 'opening', 'opportunity', 'job',
            'the', 'a', 'an', 'our', 'your', 'application'
        ]
        
        words = role.split()
        cleaned_words = [w for w in words if w.lower() not in noise_words]
        
        if not cleaned_words:
            return role.strip()
        
        cleaned_role = ' '.join(cleaned_words).strip()
        
        # Capitalize properly (title case)
        cleaned_role = cleaned_role.title()
        
        # Special cases for acronyms
        acronyms = ['Swe', 'Sre', 'Ml', 'Ai', 'Pm', 'Tpm', 'Ui', 'Ux', 'Ios', 'Aws', 'Gcp']
        for acronym in acronyms:
            if acronym in cleaned_role:
                cleaned_role = cleaned_role.replace(acronym, acronym.upper())
        
        return cleaned_role
