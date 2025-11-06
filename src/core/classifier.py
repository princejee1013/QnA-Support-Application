"""
Main classifier orchestrator.

Combines rule-based and LLM classifiers in a hybrid approach:
1. Try rule-based first (fast, free)
2. If confidence < threshold, escalate to LLM
"""

import time
from typing import Optional

from src.core.config import get_settings
from src.core.models import (
    QueryInput,
    ClassificationResult,
    ClassificationMethod
)
from src.core.rule_classifier import get_rule_classifier
from src.core.llm_classifier import get_llm_classifier
from src.utils.logger import get_logger

logger = get_logger()


class HybridClassifier:
    """
    Hybrid classifier combining rules and LLM.
    
    Strategy:
    1. Always try rule-based first (fast, free)
    2. If confidence >= threshold, return rule result
    3. If confidence < threshold, escalate to LLM
    4. Return LLM result or best available
    """
    
    def __init__(self):
        """Initialize hybrid classifier."""
        self.settings = get_settings()
        self.rule_classifier = get_rule_classifier()
        self.llm_classifier = get_llm_classifier()
        
        logger.info(
            "HybridClassifier initialized",
            confidence_threshold=self.settings.confidence_threshold
        )
    
    def classify(self, query: QueryInput) -> ClassificationResult:
        """
        Classify query using hybrid approach.
        
        Args:
            query: QueryInput with query text and metadata
            
        Returns:
            ClassificationResult from best classifier
        """
        start_time = time.time()
        
        logger.info(
            "Starting hybrid classification",
            query_length=len(query.query_text),
            user_id=query.user_id
        )
        
        # Step 1: Try rule-based classification
        rule_result = self.rule_classifier.classify(query.query_text)
        
        logger.info(
            "Rule-based classification complete",
            category=rule_result.category.value,
            confidence=rule_result.confidence
        )
        
        # Step 2: Check if confidence is sufficient
        if rule_result.confidence >= self.settings.confidence_threshold:
            logger.info(
                "Rule-based confidence sufficient, using rule result",
                confidence=rule_result.confidence,
                threshold=self.settings.confidence_threshold
            )
            return rule_result
        
        # Step 3: Escalate to LLM
        logger.info(
            "Rule-based confidence below threshold, escalating to LLM",
            rule_confidence=rule_result.confidence,
            threshold=self.settings.confidence_threshold
        )
        
        llm_result = self.llm_classifier.classify(query.query_text)
        
        logger.info(
            "LLM classification complete",
            category=llm_result.category.value,
            confidence=llm_result.confidence
        )
        
        # Step 4: Return LLM result (or rule result if LLM failed)
        if llm_result.confidence > rule_result.confidence:
            total_time_ms = (time.time() - start_time) * 1000
            
            logger.info(
                "Using LLM result",
                final_category=llm_result.category.value,
                final_confidence=llm_result.confidence,
                total_time_ms=total_time_ms
            )
            
            # Update response time to total time
            llm_result.response_time_ms = total_time_ms
            
            return llm_result
        else:
            logger.warning(
                "LLM confidence not better than rules, using rule result",
                llm_confidence=llm_result.confidence,
                rule_confidence=rule_result.confidence
            )
            return rule_result
    
    def classify_batch(self, queries: list[QueryInput]) -> list[ClassificationResult]:
        """
        Classify multiple queries.
        
        Args:
            queries: List of QueryInput objects
            
        Returns:
            List of ClassificationResult objects
        """
        logger.info(f"Starting batch classification", batch_size=len(queries))
        
        results = []
        for i, query in enumerate(queries):
            logger.debug(f"Classifying query {i+1}/{len(queries)}")
            result = self.classify(query)
            results.append(result)
        
        logger.info(f"Batch classification complete", results_count=len(results))
        
        return results


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

_default_classifier = None

def get_classifier() -> HybridClassifier:
    """
    Get hybrid classifier instance (singleton).
    
    Returns:
        HybridClassifier instance
    """
    global _default_classifier
    
    if _default_classifier is None:
        _default_classifier = HybridClassifier()
    
    return _default_classifier