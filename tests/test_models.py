"""
Tests for data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.models import (
    QueryInput,
    ClassificationResult,
    SupportCategory,
    ClassificationMethod,
    SessionMetrics,
    create_classification_result
)


# ============================================================================
# QueryInput Tests
# ============================================================================

def test_query_input_valid():
    """Test creating valid QueryInput."""
    query = QueryInput(
        query_text="My payment failed",
        user_id="user123"
    )
    
    assert query.query_text == "My payment failed"
    assert query.user_id == "user123"
    assert query.session_id is None  # Optional field defaults to None
    assert query.metadata == {}  # default_factory creates empty dict


def test_query_input_strips_whitespace():
    """Test that whitespace is automatically stripped."""
    query = QueryInput(query_text="  Help me  ")
    assert query.query_text == "Help me"  # Whitespace stripped


def test_query_input_missing_required_field():
    """Test that missing query_text raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        QueryInput(user_id="user123")  # Missing query_text
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'] == ('query_text',)
    assert errors[0]['type'] == 'missing'


def test_query_input_too_short():
    """Test that query_text must be at least 5 characters."""
    with pytest.raises(ValidationError) as exc_info:
        QueryInput(query_text="Hi")  # Only 2 characters
    
    errors = exc_info.value.errors()
    assert any('at least 5 characters' in str(e) for e in errors)


def test_query_input_empty_after_strip():
    """Test that whitespace-only query is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        QueryInput(query_text="     ")  # Only whitespace
    
    errors = exc_info.value.errors()
    # After stripping, the string is empty, so it fails min_length validation
    assert any(err['type'] == 'string_too_short' for err in errors)


# ============================================================================
# ClassificationResult Tests
# ============================================================================

def test_classification_result_valid():
    """Test creating valid ClassificationResult."""
    result = ClassificationResult(
        category=SupportCategory.BILLING,
        confidence=0.85,
        method=ClassificationMethod.RULE_BASED,
        reasoning="Matched refund keywords",
        response_time_ms=45.2
    )
    
    assert result.category == SupportCategory.BILLING
    assert result.confidence == 0.85
    assert result.method == ClassificationMethod.RULE_BASED
    assert isinstance(result.timestamp, datetime)


def test_classification_result_confidence_bounds():
    """Test that confidence must be between 0 and 1."""
    # Too high
    with pytest.raises(ValidationError):
        ClassificationResult(
            category=SupportCategory.BILLING,
            confidence=1.5,  # > 1.0
            method=ClassificationMethod.RULE_BASED,
            reasoning="Test",
            response_time_ms=10.0
        )
    
    # Too low
    with pytest.raises(ValidationError):
        ClassificationResult(
            category=SupportCategory.BILLING,
            confidence=-0.5,  # < 0.0
            method=ClassificationMethod.RULE_BASED,
            reasoning="Test",
            response_time_ms=10.0
        )


def test_classification_result_confidence_rounding():
    """Test that confidence is rounded to 2 decimal places."""
    result = ClassificationResult(
        category=SupportCategory.BILLING,
        confidence=0.856789,  # Many decimal places
        method=ClassificationMethod.RULE_BASED,
        reasoning="Test",
        response_time_ms=10.0
    )
    
    assert result.confidence == 0.86  # Rounded to 2 decimals


def test_classification_result_is_high_confidence():
    """Test the is_high_confidence method."""
    high = ClassificationResult(
        category=SupportCategory.BILLING,
        confidence=0.85,
        method=ClassificationMethod.RULE_BASED,
        reasoning="Test",
        response_time_ms=10.0
    )
    assert high.is_high_confidence() is True
    
    low = ClassificationResult(
        category=SupportCategory.BILLING,
        confidence=0.65,
        method=ClassificationMethod.RULE_BASED,
        reasoning="Test",
        response_time_ms=10.0
    )
    assert low.is_high_confidence() is False


def test_classification_result_to_display_dict():
    """Test converting to display-friendly dictionary."""
    result = ClassificationResult(
        category=SupportCategory.BILLING,
        confidence=0.85,
        method=ClassificationMethod.RULE_BASED,
        reasoning="Matched keywords",
        response_time_ms=45.7
    )
    
    display = result.to_display_dict()
    
    assert display["Category"] == "Billing & Payments"
    assert display["Confidence"] == "85%"
    assert display["Method"] == "Rule Based"
    assert display["Reasoning"] == "Matched keywords"
    assert display["Response Time"] == "46ms"


# ============================================================================
# SessionMetrics Tests
# ============================================================================

def test_session_metrics_defaults():
    """Test SessionMetrics default values."""
    metrics = SessionMetrics()
    
    assert metrics.total_queries == 0
    assert metrics.rule_based_count == 0
    assert metrics.average_confidence == 0.0
    assert metrics.category_distribution == {}


def test_session_metrics_percentages():
    """Test percentage calculations."""
    metrics = SessionMetrics(
        total_queries=100,
        rule_based_count=70,
        llm_fallback_count=30
    )
    
    assert metrics.rule_based_percentage() == 70.0
    assert metrics.llm_percentage() == 30.0


def test_session_metrics_division_by_zero():
    """Test that percentage calculations handle zero queries."""
    metrics = SessionMetrics()  # total_queries = 0
    
    assert metrics.rule_based_percentage() == 0.0
    assert metrics.llm_percentage() == 0.0
    assert metrics.average_cost_per_query() == 0.0


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_create_classification_result():
    """Test the factory function."""
    result = create_classification_result(
        category="Billing & Payments",
        confidence=0.92,
        method="rule-based",
        reasoning="Test",
        response_time_ms=50.0
    )
    
    assert isinstance(result, ClassificationResult)
    assert result.category == SupportCategory.BILLING
    assert result.method == ClassificationMethod.RULE_BASED


def test_create_classification_result_invalid_category():
    """Test that invalid category raises error."""
    with pytest.raises(ValueError):
        create_classification_result(
            category="Invalid Category",
            confidence=0.92,
            method="rule-based",
            reasoning="Test",
            response_time_ms=50.0
        )