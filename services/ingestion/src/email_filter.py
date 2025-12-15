"""
Email Relevance Filter
Pre-filters emails to identify job-related content before LLM classification
Saves API quota by filtering spam/promotional emails early
"""

import re
from typing import Tuple, Dict
from libs.core.logger import configure_logger

logger = configure_logger("email_filter")

# Job-related keywords (strong indicators)
JOB_KEYWORDS = {
    # Application related
    'application': 3,
    'applied': 3,
    'resume': 3,
    'cv': 3,
    'submission': 2,
    'apply': 2,
    
    # Interview related
    'interview': 4,
    'phone screen': 4,
    'technical interview': 4,
    'schedule': 2,
    'zoom': 1,
    'meeting': 1,
    'virtual interview': 4,
    'onsite': 3,
    'assessment': 3,
    
    # Status updates
    'offer': 4,
    'position': 2,
    'opportunity': 2,
    'regret': 3,
    'not moving forward': 3,
    'unfortunately': 2,
    'update on your application': 4,
    'status of your application': 4,
    
    # Recruiter communication
    'recruiter': 3,
    'hiring': 3,
    'talent': 2,
    'hr team': 3,
    'recruitment': 3,
    'hiring manager': 4,
    'talent acquisition': 3,
    
    # Job specifics
    'software engineer': 3,
    'developer': 2,
    'engineer': 1,
    'data scientist': 3,
    'product manager': 3,
    'designer': 1,
    'analyst': 1,
    'role': 2,
    'candidate': 2,
}

# Spam/promotional keywords (strong anti-indicators)
SPAM_KEYWORDS = {
    # Marketing
    'unsubscribe': 3,
    'opt out': 3,
    'opt-out': 3,
    'promotion': 2,
    'deal': 2,
    'discount': 2,
    'sale': 2,
    'limited time': 2,
    'act now': 2,
    'free shipping': 3,
    
    # Advertisements
    'advertisement': 3,
    'sponsored': 3,
    'featured': 2,
    'recommended for you': 2,
    'suggested': 1,
    'you might like': 2,
    
    # Social media
    'commented on': 2,
    'liked your': 2,
    'tagged you': 2,
    'connection request': 2,
    'follow': 1,
    'shared': 1,
    'posted': 1,
    
    # E-commerce
    'order confirmation': 3,
    'shipped': 3,
    'delivery': 2,
    'tracking': 2,
    'cart': 2,
    'checkout': 3,
    'invoice': 2,
    'receipt': 2,
    'payment': 2,
    
    # Newsletters
    'newsletter': 3,
    'weekly update': 2,
    'daily digest': 2,
    'subscribe': 2,
    'latest news': 2,
    
    # Notifications
    'notification': 1,
    'reminder': 1,
    'alert': 1,
    'verify': 2,
    'confirm your': 2,
    'reset password': 3,
    'security alert': 3,
    
    # Credit cards / Finance (non-job)
    'credit card': 2,
    'bank account': 2,
    'loan': 2,
    'mortgage': 2,
    'insurance': 2,
}


class EmailRelevanceFilter:
    """
    Filter emails to identify job-related content
    Returns (is_job_related, reason, confidence)
    """
    
    def __init__(self):
        self.logger = logger
        self.stats = {
            'total_checked': 0,
            'job_related': 0,
            'spam_filtered': 0
        }
    
    def is_job_related(self, email: Dict) -> Tuple[bool, str, float]:
        """
        Determine if email is job-related using keyword scoring
        
        Args:
            email: Dict with 'subject', 'body', 'from' keys
        
        Returns:
            Tuple of (is_job_related: bool, reason: str, confidence: float)
        """
        self.stats['total_checked'] += 1
        
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        from_email = email.get('from', '').lower()
        
        # Combine for analysis (weight subject more heavily)
        text = f"{subject} {subject} {body[:1000]}"  # Subject counted twice
        
        # Calculate scores
        job_score = self._calculate_score(text, JOB_KEYWORDS)
        spam_score = self._calculate_score(text, SPAM_KEYWORDS)
        
        # Check for explicit job-related patterns
        has_job_pattern = self._has_job_pattern(subject, body)
        
        # Decision logic
        decision, reason, confidence = self._make_decision(
            job_score, spam_score, has_job_pattern, subject, from_email
        )
        
        if decision:
            self.stats['job_related'] += 1
        else:
            self.stats['spam_filtered'] += 1
        
        self.logger.debug(
            f"Filter: {decision} | Job:{job_score} Spam:{spam_score} | "
            f"{subject[:50]} | {reason}"
        )
        
        return decision, reason, confidence
    
    def _calculate_score(self, text: str, keywords: Dict[str, int]) -> int:
        """Calculate weighted score based on keyword matches"""
        score = 0
        for keyword, weight in keywords.items():
            if keyword in text:
                # Count occurrences (but cap at 2 to avoid spam inflation)
                count = min(text.count(keyword), 2)
                score += weight * count
        return score
    
    def _has_job_pattern(self, subject: str, body: str) -> bool:
        """Check for explicit job-related patterns"""
        
        job_patterns = [
            r'\b(?:interview|application|position|role|opportunity)\b',
            r'\b(?:thank you for applying|application for|applied for)\b',
            r'\b(?:phone screen|technical interview|hiring manager)\b',
            r'\b(?:offer|rejection|not moving forward|regret to inform)\b',
            r'\b(?:next steps|interview process|assessment)\b',
        ]
        
        text = f"{subject} {body[:500]}".lower()
        
        for pattern in job_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _make_decision(
        self, 
        job_score: int, 
        spam_score: int, 
        has_pattern: bool,
        subject: str,
        from_email: str
    ) -> Tuple[bool, str, float]:
        """
        Make final decision on email relevance
        
        Returns:
            (is_job_related, reason, confidence)
        """
        
        # Strong job indicators
        if job_score >= 8 or has_pattern:
            confidence = min(0.95, 0.70 + (job_score * 0.03))
            return True, f"Strong job indicators (score: {job_score})", confidence
        
        # Clear spam
        if spam_score >= 6:
            confidence = min(0.95, 0.60 + (spam_score * 0.05))
            return False, f"Spam/promotional (score: {spam_score})", confidence
        
        # Job score significantly higher than spam
        if job_score >= 4 and spam_score <= 2:
            confidence = 0.70 + (job_score * 0.03)
            return True, f"Job keywords dominant ({job_score} vs {spam_score})", confidence
        
        # Spam score higher than job
        if spam_score > job_score and spam_score >= 3:
            confidence = 0.65 + (spam_score * 0.03)
            return False, f"More spam indicators ({spam_score} vs {job_score})", confidence
        
        # Check for recruiting/HR emails
        if any(domain in from_email for domain in ['greenhouse', 'lever', 'workday', 'linkedin.com', 'indeed.com']):
            if job_score > 0:
                return True, "Recruiting platform + job keywords", 0.75
        
        # Ambiguous - default to keeping (better to over-include)
        # This ensures we don't accidentally filter real job emails
        if job_score > 0:
            return True, f"Ambiguous but has job keywords ({job_score})", 0.50
        
        # Very likely spam
        if spam_score >= 2:
            return False, f"Likely spam ({spam_score} spam keywords)", 0.60
        
        # Complete uncertainty - keep to be safe
        return True, "No clear indicators, keeping", 0.30
    
    def get_stats(self) -> Dict:
        """Get filtering statistics"""
        if self.stats['total_checked'] == 0:
            return {
                'total': 0,
                'job_related': 0,
                'spam_filtered': 0,
                'spam_rate': 0.0,
                'api_calls_saved': 0
            }
        
        return {
            'total': self.stats['total_checked'],
            'job_related': self.stats['job_related'],
            'spam_filtered': self.stats['spam_filtered'],
            'spam_rate': (self.stats['spam_filtered'] / self.stats['total_checked']) * 100,
            'api_calls_saved': self.stats['spam_filtered']  # Each filtered email saves 1 LLM call
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_checked': 0,
            'job_related': 0,
            'spam_filtered': 0
        }
