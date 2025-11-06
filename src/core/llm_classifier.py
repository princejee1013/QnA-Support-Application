"""
LLM-based classifier using Azure OpenAI.

This is the fallback classifier for queries that rule-based
classification cannot handle confidently.
"""

import json
import time
from typing import Optional, Dict, Any

from openai import AzureOpenAI
from openai import APIError, RateLimitError, APITimeoutError

from src.core.config import get_settings
from src.core.models import (
    ClassificationResult,
    SupportCategory,
    ClassificationMethod
)
from src.utils.prompts import get_classification_prompt
from src.utils.logger import get_logger

logger = get_logger()


class LLMClassifier:
    """
    LLM-based classifier using Azure OpenAI.
    
    Features:
    - Structured JSON output
    - Retry logic with exponential backoff
    - Token usage tracking
    - Cost estimation
    - Error handling
    """
    
    def __init__(self):
        """Initialize LLM classifier with Azure OpenAI client."""
        settings = get_settings()
        
        try:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            
            self.deployment_name = settings.azure_openai_deployment_name
            self.max_tokens = settings.max_tokens
            self.temperature = settings.temperature
            
            logger.info(
                "LLMClassifier initialized",
                deployment=self.deployment_name,
                endpoint=settings.azure_openai_endpoint
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def classify(
        self,
        query_text: str,
        max_retries: int = 3
    ) -> ClassificationResult:
        """
        Classify query using Azure OpenAI.
        
        Args:
            query_text: The support query to classify
            max_retries: Maximum retry attempts on failure
            
        Returns:
            ClassificationResult with LLM classification
        """
        start_time = time.time()
        
        logger.info("Starting LLM classification", query_length=len(query_text))
        
        # Generate prompt
        prompt = get_classification_prompt(query_text)
        
        # Call LLM with retries
        for attempt in range(1, max_retries + 1):
            try:
                response = self._call_llm(prompt)
                
                # Parse response
                result = self._parse_response(response, query_text, start_time)
                
                logger.info(
                    "LLM classification successful",
                    category=result.category.value,
                    confidence=result.confidence,
                    tokens_used=result.llm_tokens_used,
                    attempt=attempt
                )
                
                return result
                
            except RateLimitError as e:
                logger.warning(
                    f"Rate limit hit, retrying ({attempt}/{max_retries})",
                    error=str(e)
                )
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    return self._create_fallback_result(query_text, start_time, str(e))
            
            except (APIError, APITimeoutError) as e:
                logger.error(f"API error on attempt {attempt}: {e}")
                
                if attempt < max_retries:
                    time.sleep(1)
                else:
                    return self._create_fallback_result(query_text, start_time, str(e))
            
            except Exception as e:
                logger.error(f"Unexpected error during LLM classification: {e}")
                return self._create_fallback_result(query_text, start_time, str(e))
        
        # Should never reach here, but just in case
        return self._create_fallback_result(
            query_text,
            start_time,
            "Max retries exceeded"
        )
    
    def _call_llm(self, prompt: str) -> Any:
        """
        Make API call to Azure OpenAI.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            API response object
        """
        logger.debug("Calling Azure OpenAI API")
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,  # This is your deployment name
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise support query classifier. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}  # Ensures JSON output
        )
        
        return response
    
    def _parse_response(
        self,
        response: Any,
        query_text: str,
        start_time: float
    ) -> ClassificationResult:
        """
        Parse LLM response into ClassificationResult.
        
        Args:
            response: API response object
            query_text: Original query
            start_time: Classification start time
            
        Returns:
            ClassificationResult
        """
        # Extract content
        content = response.choices[0].message.content
        
        logger.debug("Parsing LLM response", content_length=len(content))
        
        try:
            # Parse JSON
            parsed = json.loads(content)
            
            category_str = parsed.get('category', 'General Inquiry')
            confidence = float(parsed.get('confidence', 0.5))
            reasoning = parsed.get('reasoning', 'LLM classification')
            sentiment = parsed.get('sentiment', 'neutral')
            urgency = parsed.get('urgency', 'normal')
            
            # Add sentiment/urgency to reasoning if present
            if sentiment != 'neutral' or urgency != 'normal':
                reasoning = f"{reasoning} [Sentiment: {sentiment}, Urgency: {urgency}]"
            
            # Validate category
            try:
                category = SupportCategory(category_str)
            except ValueError:
                logger.warning(
                    f"Invalid category from LLM: {category_str}, using General"
                )
                category = SupportCategory.GENERAL
            
            # Get token usage
            tokens_used = response.usage.total_tokens
            
            # Estimate cost (GPT-4o-mini pricing: ~$0.15/1M input, ~$0.60/1M output)
            # Rough estimate: $0.0004 per 1K tokens average
            estimated_cost = (tokens_used / 1000) * 0.0004
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return ClassificationResult(
                category=category,
                confidence=min(confidence, 0.95),  # Cap at 0.95
                method=ClassificationMethod.LLM_FALLBACK,
                reasoning=reasoning,
                response_time_ms=response_time_ms,
                llm_tokens_used=tokens_used,
                estimated_cost=estimated_cost
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response content: {content}")
            
            # Fallback
            return self._create_fallback_result(
                query_text,
                start_time,
                "JSON parse error"
            )
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._create_fallback_result(
                query_text,
                start_time,
                str(e)
            )
    
    def _create_fallback_result(
        self,
        query_text: str,
        start_time: float,
        error_msg: str
    ) -> ClassificationResult:
        """
        Create fallback result when LLM fails.
        
        Args:
            query_text: Original query
            start_time: Start time
            error_msg: Error message
            
        Returns:
            ClassificationResult with low confidence
        """
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.warning("Using fallback classification due to LLM error")
        
        return ClassificationResult(
            category=SupportCategory.GENERAL,
            confidence=0.3,
            method=ClassificationMethod.LLM_FALLBACK,
            reasoning=f"LLM classification failed: {error_msg}",
            response_time_ms=response_time_ms
        )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

_default_llm_classifier = None

def get_llm_classifier() -> LLMClassifier:
    """
    Get LLM classifier instance (singleton).
    
    Returns:
        LLMClassifier instance
    """
    global _default_llm_classifier
    
    if _default_llm_classifier is None:
        _default_llm_classifier = LLMClassifier()
    
    return _default_llm_classifier