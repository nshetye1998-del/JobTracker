"""
KeywordLearner: Self-Learning Keyword Classification System

This module implements a keyword-based classification system that:
1. Uses base keywords for obvious cases (instant, free)
2. Learns new patterns from AI classifications
3. Learns from user corrections
4. Validates keyword accuracy over time
5. Automatically deactivates poor-performing keywords

The system gets smarter every day without manual intervention.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import re
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class KeywordLearner:
    """
    Self-learning keyword system that improves accuracy over time
    """
    
    def __init__(self, db_conn):
        """
        Initialize keyword learner
        
        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn
        self.min_confidence = 0.85
        self.min_matches_for_validation = 10
        logger.info("KeywordLearner initialized")
    
    def load_active_keywords(self) -> Dict[str, List[Dict]]:
        """
        Load all active keywords grouped by classification
        
        Returns:
            Dictionary of keywords grouped by classification type
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    keyword_phrase, 
                    classification, 
                    confidence,
                    accuracy,
                    times_matched,
                    id
                FROM keyword_patterns
                WHERE is_active = true
                AND (
                    times_matched < %s 
                    OR accuracy >= %s
                )
                ORDER BY confidence DESC
            """, (self.min_matches_for_validation, self.min_confidence))
            
            keywords = cursor.fetchall()
            cursor.close()
            
            # Group by classification
            grouped = {
                'INTERVIEW': [],
                'REJECTION': [],
                'OFFER': [],
                'OTHER': []
            }
            
            for kw in keywords:
                classification = kw['classification']
                if classification in grouped:
                    grouped[classification].append(dict(kw))
            
            total_keywords = sum(len(kws) for kws in grouped.values())
            logger.info(f"Loaded {total_keywords} active keywords")
            
            return grouped
            
        except Exception as e:
            logger.error(f"Error loading keywords: {e}")
            return {
                'INTERVIEW': [],
                'REJECTION': [],
                'OFFER': [],
                'OTHER': []
            }
    
    def quick_classify(self, email_text: str) -> Optional[Dict]:
        """
        Quick classification using keywords (instant, no API calls)
        
        Args:
            email_text: Combined email subject and body
            
        Returns:
            Classification result dict or None if no confident match
        """
        if not email_text:
            return None
            
        email_text_lower = email_text.lower()
        keywords = self.load_active_keywords()
        
        # Check each classification type
        # Order matters: INTERVIEW > OFFER > REJECTION > OTHER
        priority_order = ['INTERVIEW', 'OFFER', 'REJECTION', 'OTHER']
        
        for classification in priority_order:
            keyword_list = keywords.get(classification, [])
            
            for kw in keyword_list:
                if kw['keyword_phrase'].lower() in email_text_lower:
                    # Found a match!
                    self.increment_keyword_usage(kw['id'])
                    
                    logger.info(f"Keyword match: '{kw['keyword_phrase']}' → {classification} (confidence: {kw['confidence']:.2f})")
                    
                    return {
                        'classification': classification,
                        'confidence': kw['confidence'],
                        'method': 'keyword',
                        'keyword_id': kw['id'],
                        'keyword_phrase': kw['keyword_phrase']
                    }
        
        logger.debug("No keyword match found")
        return None
    
    def increment_keyword_usage(self, keyword_id: int):
        """
        Increment usage counter for keyword
        
        Args:
            keyword_id: ID of the keyword pattern
        """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE keyword_patterns
                SET times_matched = times_matched + 1,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (keyword_id,))
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error incrementing keyword usage: {e}")
            self.db_conn.rollback()
    
    def learn_from_ai_classification(self, email_text: str, classification: str, confidence: float):
        """
        Extract and learn new keyword patterns from AI classification
        
        Args:
            email_text: The email text that was classified
            classification: The classification assigned by AI
            confidence: Confidence score from AI (0-1)
        """
        if confidence < 0.90:
            # Only learn from high-confidence AI classifications
            return
        
        # Extract potential key phrases
        patterns = self.extract_key_phrases(email_text, classification)
        
        learned_count = 0
        for phrase in patterns:
            if self.add_or_update_keyword(phrase, classification, confidence, 'ai'):
                learned_count += 1
        
        if learned_count > 0:
            logger.info(f"Learned {learned_count} new keywords from AI classification")
    
    def extract_key_phrases(self, text: str, classification: str) -> List[str]:
        """
        Extract potential keyword phrases from text
        
        Args:
            text: Email text to extract from
            classification: The classification type
            
        Returns:
            List of potential keyword phrases
        """
        text_lower = text.lower()
        phrases = []
        
        # Interview-specific patterns
        if classification == 'INTERVIEW':
            patterns = [
                r'schedule (?:a|an|the) (?:interview|call|meeting)',
                r'interview (?:invitation|scheduled|confirmation)',
                r'would like to (?:interview|speak with|meet)',
                r'phone (?:screen|interview)',
                r'technical (?:interview|assessment|challenge)',
                r'video (?:interview|call)',
                r'zoom (?:interview|meeting)',
                r'teams (?:interview|meeting)',
                r'onsite (?:interview|visit)',
                r'next (?:step|round)',
                r'move forward with',
                r'discuss (?:your|the) (?:application|role)',
                r'hiring (?:manager|team) would like'
            ]
        
        # Rejection-specific patterns
        elif classification == 'REJECTION':
            patterns = [
                r'not (?:moving forward|selected|proceed|the right fit)',
                r'(?:decided|chosen) to pursue other',
                r'regret to (?:inform|tell)',
                r'will not be (?:proceeding|continuing|moving)',
                r'position has been filled',
                r'different (?:direction|candidate)',
                r'other candidates',
                r'better (?:fit|match)',
                r'keep (?:your|you) (?:resume|application) on file',
                r'(?:unfortunately|sadly)',
                r'wish you (?:the best|success)'
            ]
        
        # Offer-specific patterns
        elif classification == 'OFFER':
            patterns = [
                r'(?:pleased|happy|excited) to (?:offer|extend)',
                r'offer (?:letter|of employment)',
                r'employment offer',
                r'accept (?:our|the) offer',
                r'extend (?:an|the) offer',
                r'job offer',
                r'start date',
                r'compensation (?:package|details)',
                r'salary (?:of|is)',
                r'benefits package'
            ]
        
        # Other/General patterns
        else:
            patterns = [
                r'received (?:your|the) application',
                r'application (?:received|status)',
                r'reviewing (?:your|the) application',
                r'thank you for applying'
            ]
        
        # Extract matches
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Convert match to string if it's a tuple
                for match in matches:
                    if isinstance(match, tuple):
                        phrase = ' '.join(match)
                    else:
                        phrase = match
                    phrases.append(phrase.strip())
        
        return list(set(phrases))  # Remove duplicates
    
    def add_or_update_keyword(self, phrase: str, classification: str, confidence: float, learned_from: str) -> bool:
        """
        Add new keyword or update existing
        
        Args:
            phrase: Keyword phrase
            classification: Classification type
            confidence: Confidence score (0-1)
            learned_from: Source ('ai', 'user_correction', 'base')
            
        Returns:
            True if keyword was added, False otherwise
        """
        if not phrase or len(phrase) < 3:
            return False
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO keyword_patterns 
                (keyword_phrase, classification, confidence, learned_from, times_matched, times_correct)
                VALUES (%s, %s, %s, %s, 1, 1)
                ON CONFLICT (keyword_phrase, classification) DO NOTHING
                RETURNING id
            """, (phrase, classification, confidence, learned_from))
            
            result = cursor.fetchone()
            self.db_conn.commit()
            cursor.close()
            
            if result:
                logger.info(f"Learned new keyword: '{phrase}' → {classification} (confidence: {confidence:.2f})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            self.db_conn.rollback()
            return False
    
    def record_classification_result(self, email_id: str, method: str, 
                                    initial_classification: str, 
                                    final_classification: str,
                                    confidence: float = 0.0,
                                    keyword_id: Optional[int] = None):
        """
        Record classification result for learning
        
        Args:
            email_id: Email identifier
            method: Classification method ('keyword', 'ai', 'user_correction')
            initial_classification: Initial classification assigned
            final_classification: Final classification (after validation)
            confidence: Confidence score
            keyword_id: ID of keyword used (if method='keyword')
        """
        was_correct = (initial_classification == final_classification)
        
        try:
            cursor = self.db_conn.cursor()
            
            # Record feedback
            cursor.execute("""
                INSERT INTO classification_feedback
                (email_id, classification_method, keyword_id, 
                 initial_classification, final_classification, was_correct, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email_id, method, keyword_id, initial_classification, 
                  final_classification, was_correct, confidence))
            
            # If keyword was used, update its accuracy
            if keyword_id and method == 'keyword':
                cursor.execute("""
                    UPDATE keyword_patterns
                    SET times_correct = times_correct + %s,
                        accuracy = CASE 
                            WHEN times_matched > 0 THEN (times_correct + %s)::FLOAT / times_matched::FLOAT
                            ELSE 0
                        END
                    WHERE id = %s
                """, (1 if was_correct else 0, 1 if was_correct else 0, keyword_id))
            
            self.db_conn.commit()
            cursor.close()
            
            logger.debug(f"Recorded classification feedback: {method} → {final_classification} (correct: {was_correct})")
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            self.db_conn.rollback()
    
    def deactivate_low_accuracy_keywords(self):
        """
        Deactivate keywords with poor accuracy after sufficient validation
        """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE keyword_patterns
                SET is_active = false
                WHERE times_matched >= %s
                AND accuracy < %s
                AND is_active = true
                RETURNING keyword_phrase, classification, accuracy
            """, (self.min_matches_for_validation, self.min_confidence))
            
            deactivated = cursor.fetchall()
            self.db_conn.commit()
            cursor.close()
            
            if deactivated:
                logger.warning(f"Deactivated {len(deactivated)} low-accuracy keywords:")
                for phrase, classification, accuracy in deactivated:
                    logger.warning(f"  - '{phrase}' ({classification}) - accuracy: {accuracy:.2%}")
            else:
                logger.debug("No keywords to deactivate")
                
        except Exception as e:
            logger.error(f"Error deactivating keywords: {e}")
            self.db_conn.rollback()
    
    def get_statistics(self) -> Dict:
        """
        Get keyword learning statistics
        
        Returns:
            Dictionary of statistics
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_keywords,
                    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_keywords,
                    SUM(times_matched) as total_matches,
                    AVG(accuracy) as avg_accuracy,
                    SUM(CASE WHEN learned_from = 'base' THEN 1 ELSE 0 END) as base_keywords,
                    SUM(CASE WHEN learned_from = 'ai' THEN 1 ELSE 0 END) as ai_learned,
                    SUM(CASE WHEN learned_from = 'user_correction' THEN 1 ELSE 0 END) as user_corrections
                FROM keyword_patterns
            """)
            
            stats = dict(cursor.fetchone())
            cursor.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
