"""
Data models for QnA Support Application.

This module defines all data structures using Pydantic for:
- Type safety
- Runtime validation
- Automatic serialization
- Self-documenting code
"""

from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# ENUMS (Predefined Choices)
# ============================================================================

class SupportCategory(str, Enum):
    """
    Allowed support ticket categories.
    
    Using Enum ensures only valid categories are used throughout the app.
    """
    BILLING = "Billing & Payments"
    TECHNICAL = "Technical Issues"
    ACCOUNT = "Account Management"
    PRODUCT = "Product Questions"
    FEATURE = "Feature Requests"
    BUG = "Bug Reports"
    GENERAL = "General Inquiry"


class ClassificationMethod(str, Enum):
    """How the query was classified."""
    RULE_BASED = "rule-based"
    LLM_FALLBACK = "llm-fallback"
    HYBRID = "hybrid"




# ============================================================================
# INPUT MODELS
# ============================================================================

class QueryInput(BaseModel):
    """
    User's support query input.
    
    This is the data we receive from the user through Streamlit UI.
    """
    
    query_text: str = Field(
        ...,  # ... means required (no default)
        min_length=5,
        max_length=2000,
        description="The support query text",
        examples=["My payment failed but I was charged twice"]
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user identifier for tracking"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for correlating multiple queries"
    )
    
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., user agent, timestamp)"
    )
    
    # Pydantic v2 configuration
    model_config = ConfigDict(
        str_strip_whitespace=True,  # Auto-trim whitespace
        json_schema_extra={
            "examples": [
                {
                    "query_text": "How do I get a refund for my subscription?",
                    "user_id": "user_123",
                    "session_id": "session_abc"
                }
            ]
        }
    )
    
    @field_validator('query_text')
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Ensure query is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('query_text')
    @classmethod
    def validate_query_language(cls, v: str) -> str:
        """Basic check that query contains some alphabetic characters."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Query must contain at least some text")
        return v




# ============================================================================
# OUTPUT MODELS
# ============================================================================

class RuleMatch(BaseModel):
    """Details about a rule-based classification match."""
    
    rule_category: SupportCategory
    matched_keywords: List[str] = Field(default_factory=list)
    matched_patterns: List[str] = Field(default_factory=list)
    score: float = Field(ge=0.0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "rule_category": "Billing & Payments",
                    "matched_keywords": ["refund", "charge"],
                    "matched_patterns": ["refund.*request"],
                    "score": 2.5
                }
            ]
        }
    )


class ClassificationResult(BaseModel):
    """
    Result of query classification.
    
    This is the main output model containing all classification information.
    """
    
    # Core results
    category: SupportCategory = Field(
        description="Classified support category"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    
    method: ClassificationMethod = Field(
        description="Classification method used"
    )
    
    reasoning: str = Field(
        min_length=1,
        max_length=500,
        description="Explanation of classification decision"
    )
    
    # Metadata
    response_time_ms: float = Field(
        ge=0.0,
        description="Time taken to classify (milliseconds)"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When classification occurred"
    )
    
    # Optional details
    rule_matches: Optional[List[RuleMatch]] = Field(
        default=None,
        description="Details of rule-based matches (if applicable)"
    )
    
    llm_tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of tokens used if LLM was called"
    )
    
    estimated_cost: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Estimated API cost in USD"
    )
    
    # Multi-intent detection
    is_multi_intent: bool = Field(
        default=False,
        description="True if multiple intents detected in the query"
    )
    
    additional_categories: List[SupportCategory] = Field(
        default_factory=list,
        description="Other categories detected with significant confidence"
    )
    
    category_scores: Optional[dict] = Field(
        default=None,
        description="Confidence scores for all categories (for debugging)"
    )
    
    routing_priority: str = Field(
        default="normal",
        description="Suggested routing priority: critical, high, normal, low"
    )
    
    requires_human_review: bool = Field(
        default=False,
        description="True if query should be reviewed by human agent"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": "Billing & Payments",
                    "confidence": 0.92,
                    "method": "rule-based",
                    "reasoning": "Matched keywords: refund, charge",
                    "response_time_ms": 45.2,
                    "timestamp": "2024-01-15T14:23:45.123456",
                    "is_multi_intent": False,
                    "additional_categories": [],
                    "routing_priority": "normal",
                    "requires_human_review": False
                }
            ]
        }
    )
    
    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Round confidence to 2 decimal places."""
        return round(v, 2)
    
    def is_high_confidence(self) -> bool:
        """Check if classification has high confidence."""
        return self.confidence >= 0.7
    
    def to_display_dict(self) -> dict:
        """
        Convert to dict suitable for display in UI.
        
        This formats data nicely for Streamlit display.
        """
        return {
            "Category": self.category.value,
            "Confidence": f"{self.confidence:.0%}",
            "Method": self.method.value.replace('-', ' ').title(),
            "Reasoning": self.reasoning,
            "Response Time": f"{self.response_time_ms:.0f}ms"
        }
    



# ============================================================================
# METRICS MODELS
# ============================================================================

class SessionMetrics(BaseModel):
    """
    Aggregated metrics for a session.
    
    Used for analytics dashboard in Streamlit.
    """
    
    total_queries: int = Field(ge=0, default=0)
    
    rule_based_count: int = Field(ge=0, default=0)
    llm_fallback_count: int = Field(ge=0, default=0)
    
    average_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    average_response_time_ms: float = Field(ge=0.0, default=0.0)
    
    total_tokens_used: int = Field(ge=0, default=0)
    estimated_total_cost: float = Field(ge=0.0, default=0.0)
    
    category_distribution: dict[str, int] = Field(default_factory=dict)
    
    def rule_based_percentage(self) -> float:
        """Calculate percentage of queries handled by rules."""
        if self.total_queries == 0:
            return 0.0
        return (self.rule_based_count / self.total_queries) * 100
    
    def llm_percentage(self) -> float:
        """Calculate percentage of queries that needed LLM."""
        if self.total_queries == 0:
            return 0.0
        return (self.llm_fallback_count / self.total_queries) * 100
    
    def average_cost_per_query(self) -> float:
        """Calculate average cost per query."""
        if self.total_queries == 0:
            return 0.0
        return self.estimated_total_cost / self.total_queries


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_classification_result(
    category: str,
    confidence: float,
    method: str,
    reasoning: str,
    response_time_ms: float,
    **kwargs
) -> ClassificationResult:
    """
    Factory function to create ClassificationResult.
    
    This provides a convenient way to create results with validation.
    
    Args:
        category: Category name (converted to enum)
        confidence: Confidence score
        method: Classification method
        reasoning: Explanation
        response_time_ms: Processing time
        **kwargs: Additional optional fields
        
    Returns:
        Validated ClassificationResult
        
    Example:
        >>> result = create_classification_result(
        ...     category="Billing & Payments",
        ...     confidence=0.92,
        ...     method="rule-based",
        ...     reasoning="Matched refund keywords",
        ...     response_time_ms=45.2
        ... )
    """
    # Convert string category to enum
    category_enum = SupportCategory(category)
    method_enum = ClassificationMethod(method)
    
    return ClassificationResult(
        category=category_enum,
        confidence=confidence,
        method=method_enum,
        reasoning=reasoning,
        response_time_ms=response_time_ms,
        **kwargs
    )