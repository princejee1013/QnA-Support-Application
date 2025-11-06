"""
Rule-based classifier for support queries.

Fast, deterministic classification using keyword patterns and rules.
No LLM calls = free and instant!
"""

import re
from functools import lru_cache
from typing import Dict, List, Tuple

from src.core.models import ClassificationResult, SupportCategory, ClassificationMethod
from src.core.preprocessor import get_preprocessor
from src.utils.logger import get_logger

logger = get_logger()


# ============================================================================
# KEYWORD PATTERNS FOR EACH CATEGORY
# ============================================================================

# Keywords and phrases that indicate each category
# Format: {category: [(keywords, weight), ...]}
CATEGORY_PATTERNS = {
    SupportCategory.BILLING: [
        # Strong indicators (high confidence)
        (['refund', 'charged', 'charge', 'payment', 'bill', 'invoice'], 0.9),
        (['money', 'paid', 'cost', 'price', 'fee', 'dollars'], 0.8),
        (['subscription', 'cancel', 'upgrade', 'downgrade'], 0.85),
        (['credit card', 'debit card', 'payment method'], 0.9),
        
        # High confidence - refund/overcharge situations
        (['money back', 'refund', 'charged twice', 'double charged'], 0.95),
        (['overcharged', 'unauthorized', 'incorrect charge'], 0.95),
        
        # Medium indicators
        (['receipt', 'transaction', 'purchase'], 0.75),
    ],
    
    SupportCategory.TECHNICAL: [
        # Strong indicators
        (['error', 'bug', 'crash', 'broken', 'not working'], 0.9),
        (['loading', 'slow', 'timeout', 'connection'], 0.8),
        (['feature', 'function', 'button', 'click'], 0.75),
        
        # Medium indicators
        (['browser', 'app', 'mobile', 'desktop'], 0.7),
        (['update', 'version', 'install'], 0.75),
    ],
    
    SupportCategory.ACCOUNT: [
        # Strong indicators - Password/Login/Access issues
        (['forgot password', 'reset password', 'forgot my password'], 0.95),
        (['password', 'login', 'log in', 'sign in', 'access'], 0.85),
        (['locked out', 'cant access', "can't access", 'cannot access'], 0.9),
        
        # Account management
        (['account', 'profile', 'settings', 'preferences'], 0.85),
        (['email', 'username', 'change', 'update'], 0.8),
        (['delete account', 'close account', 'deactivate'], 0.95),
        (['personal information', 'details', 'data'], 0.8),
        
        # Medium indicators
        (['verify', 'verification', 'confirm'], 0.75),
        (['security', 'privacy', 'permissions'], 0.8),
    ],
    
    SupportCategory.FEATURE: [
        # Strong indicators - Feature requests
        (['add feature', 'new feature', 'feature request'], 0.95),
        (['can you add', 'could you add', 'please add'], 0.9),
        (['would like', 'wish', 'hope', 'suggestion'], 0.85),
        (['export', 'download', 'import', 'integrate'], 0.8),
        
        # Enhancement requests
        (['improve', 'enhancement', 'better', 'easier'], 0.75),
        (['missing', 'need', 'want', 'require'], 0.7),
    ],
    
    SupportCategory.BUG: [
        # Strong indicators - Bug reports
        (['bug', 'issue', 'problem', 'defect'], 0.9),
        (['unexpected', 'incorrect', 'wrong', 'broken'], 0.85),
        (['should work', 'supposed to', 'expected'], 0.8),
        
        # Error indicators (overlap with TECHNICAL, but more specific)
        (['always fails', 'consistently', 'reproducible'], 0.85),
    ],
    
    SupportCategory.GENERAL: [
        # General/fallback patterns (low confidence)
        (['help', 'support', 'question', 'how'], 0.5),
        (['what', 'why', 'when', 'where'], 0.4),
        (['information', 'about', 'learn'], 0.45),
    ],
}


# ============================================================================
# RULE CLASSIFIER CLASS
# ============================================================================

class RuleBasedClassifier:
    """
    Fast rule-based classifier using keyword matching.
    
    How it works:
    1. Preprocess query text
    2. Extract keywords
    3. Match against category patterns
    4. Calculate confidence scores
    5. Return best match
    """
    
    def __init__(self):
        """Initialize rule-based classifier."""
        self.preprocessor = get_preprocessor()
        self.patterns = CATEGORY_PATTERNS
        
        logger.debug(
            "RuleBasedClassifier initialized",
            categories=len(self.patterns)
        )
    
    def classify(self, query_text: str) -> ClassificationResult:
        """
        Classify query using keyword patterns.
        
        Args:
            query_text: Raw query text from user
            
        Returns:
            ClassificationResult with category and confidence
        """
        import time
        start_time = time.time()
        
        # Preprocess text
        cleaned_text = self.preprocessor.preprocess(query_text)
        keywords = self.preprocessor.extract_keywords(query_text)
        
        logger.debug(
            "Classifying with rules",
            original_length=len(query_text),
            cleaned_length=len(cleaned_text),
            keywords_count=len(keywords)
        )
        
        # Calculate scores for each category
        category_scores = self._calculate_category_scores(
            cleaned_text,
            keywords
        )
        
        # Get best category
        best_category, confidence = self._get_best_category(category_scores)
        
        # Detect multi-intent: Find other high-confidence categories
        additional_categories, is_multi_intent = self._detect_multi_intent(
            category_scores,
            best_category
        )
        
        # Create matched patterns list for explanation
        matched_patterns = self._get_matched_patterns(
            best_category,
            keywords
        )
        
        # Determine routing priority and human review need
        routing_priority, requires_human = self._determine_routing(
            best_category,
            confidence,
            is_multi_intent,
            query_text
        )
        
        # Build reasoning
        reasoning = f"Matched {len(matched_patterns)} patterns: {', '.join(matched_patterns[:3])}"
        if is_multi_intent:
            other_cats = ', '.join([cat.value for cat in additional_categories])
            reasoning += f" | Also detected: {other_cats}"
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Rule-based classification complete",
            category=best_category.value,
            confidence=confidence,
            matches=len(matched_patterns),
            is_multi_intent=is_multi_intent,
            additional_categories=[c.value for c in additional_categories],
            routing_priority=routing_priority,
            response_time_ms=response_time_ms
        )
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            reasoning=reasoning,
            method=ClassificationMethod.RULE_BASED,
            response_time_ms=response_time_ms,
            is_multi_intent=is_multi_intent,
            additional_categories=additional_categories,
            category_scores={cat.value: score for cat, score in category_scores.items()},
            routing_priority=routing_priority,
            requires_human_review=requires_human
        )
    
    def _calculate_category_scores(
        self,
        text: str,
        keywords: List[str]
    ) -> Dict[SupportCategory, float]:
        """
        Calculate confidence score for each category.
        
        Args:
            text: Preprocessed text
            keywords: Extracted keywords
            
        Returns:
            Dict mapping category to confidence score
        """
        scores = {}
        
        for category, pattern_groups in self.patterns.items():
            total_score = 0.0
            match_count = 0
            
            for pattern_keywords, weight in pattern_groups:
                # Check if any pattern keyword is in our keywords
                matches = sum(
                    1 for pk in pattern_keywords
                    if pk in keywords or pk in text
                )
                
                if matches > 0:
                    # Score based on match ratio and weight
                    match_ratio = matches / len(pattern_keywords)
                    total_score += match_ratio * weight
                    match_count += 1
            
            # Normalize score (cap at 1.0)
            if match_count > 0:
                # Use weighted sum instead of average for better scoring
                # More matches = higher confidence
                # Boost for multiple pattern matches
                boost = min(0.15 * (match_count - 1), 0.35)
                final_score = min(total_score + boost, 1.0)
            else:
                final_score = 0.0
            
            scores[category] = final_score
        
        return scores
    
    def _get_best_category(
        self,
        scores: Dict[SupportCategory, float]
    ) -> Tuple[SupportCategory, float]:
        """
        Get category with highest score.
        
        Args:
            scores: Category scores
            
        Returns:
            (best_category, confidence_score)
        """
        if not scores:
            return SupportCategory.GENERAL, 0.3
        
        best_category = max(scores.items(), key=lambda x: x[1])
        
        # If all scores are very low, default to GENERAL with low confidence
        if best_category[1] < 0.2:
            return SupportCategory.GENERAL, 0.3
        
        return best_category
    
    def _get_matched_patterns(
        self,
        category: SupportCategory,
        keywords: List[str]
    ) -> List[str]:
        """
        Get list of matched pattern keywords for explanation.
        
        Args:
            category: Matched category
            keywords: Extracted keywords from query
            
        Returns:
            List of matched pattern keywords
        """
        matched = []
        
        if category not in self.patterns:
            return matched
        
        for pattern_keywords, _ in self.patterns[category]:
            for pk in pattern_keywords:
                if pk in keywords:
                    matched.append(pk)
        
        return list(set(matched))  # Remove duplicates
    
    def _detect_multi_intent(
        self,
        scores: Dict[SupportCategory, float],
        primary_category: SupportCategory
    ) -> Tuple[List[SupportCategory], bool]:
        """
        Detect if query has multiple intents.
        
        Args:
            scores: Category confidence scores
            primary_category: Highest scoring category
            
        Returns:
            (additional_categories, is_multi_intent)
        """
        # Threshold for considering a category as "additional intent"
        MULTI_INTENT_THRESHOLD = 0.5
        
        # Find categories with significant confidence (but not primary)
        additional = [
            category
            for category, score in scores.items()
            if category != primary_category and score >= MULTI_INTENT_THRESHOLD
        ]
        
        # Sort by score descending
        additional.sort(key=lambda c: scores[c], reverse=True)
        
        is_multi_intent = len(additional) > 0
        
        logger.debug(
            "Multi-intent detection",
            primary=primary_category.value,
            additional=[c.value for c in additional],
            is_multi_intent=is_multi_intent
        )
        
        return additional, is_multi_intent
    
    def _determine_routing(
        self,
        category: SupportCategory,
        confidence: float,
        is_multi_intent: bool,
        query_text: str
    ) -> Tuple[str, bool]:
        """
        Determine routing priority and if human review is needed.
        
        Args:
            category: Classified category
            confidence: Classification confidence
            is_multi_intent: Whether multiple intents detected
            query_text: Original query
            
        Returns:
            (routing_priority, requires_human_review)
        """
        query_lower = query_text.lower()
        
        # Emergency/Critical keywords
        critical_keywords = [
            'urgent', 'emergency', 'critical', 'asap', 'immediately',
            'can\'t access', 'cannot access', 'locked out', 'fraud',
            'unauthorized', 'hacked', 'stolen', 'security breach'
        ]
        
        # High priority keywords
        high_keywords = [
            'crash', 'error', 'down', 'not working', 'broken',
            'charged twice', 'double charge', 'refund', 'money back',
            'forgot password', 'reset password'
        ]
        
        # Check for critical issues
        has_critical = any(kw in query_lower for kw in critical_keywords)
        has_high = any(kw in query_lower for kw in high_keywords)
        
        # Determine priority
        if has_critical:
            priority = "critical"
        elif has_high or is_multi_intent:
            priority = "high"
        elif confidence < 0.5:
            priority = "high"  # Low confidence needs review
        else:
            priority = "normal"
        
        # Determine if human review needed
        requires_human = (
            is_multi_intent or  # Multiple intents need human triage
            has_critical or  # Critical issues need human attention
            confidence < 0.4 or  # Very low confidence
            (category == SupportCategory.BILLING and has_high)  # Billing + refund
        )
        
        logger.debug(
            "Routing determination",
            priority=priority,
            requires_human=requires_human,
            is_multi_intent=is_multi_intent,
            confidence=confidence,
            has_critical=has_critical,
            has_high=has_high
        )
        
        return priority, requires_human


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

@lru_cache()
def get_rule_classifier() -> RuleBasedClassifier:
    """
    Get rule-based classifier singleton.
    
    Returns:
        Cached RuleBasedClassifier instance
    """
    return RuleBasedClassifier()
