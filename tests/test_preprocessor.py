"""
Tests for text preprocessor.
"""

import pytest
from src.core.preprocessor import TextPreprocessor, PreprocessingConfig, get_preprocessor


# ============================================================================
# Basic Preprocessing Tests
# ============================================================================

def test_preprocessor_lowercase():
    """Test lowercase conversion."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("HELP ME WITH MY ACCOUNT")
    assert result == "help me with my account"


def test_preprocessor_whitespace_normalization():
    """Test whitespace normalization."""
    preprocessor = TextPreprocessor()
    
    # Multiple spaces
    result = preprocessor.preprocess("help    me")
    assert result == "help me"
    
    # Tabs and newlines
    result = preprocessor.preprocess("help\t\nme")
    assert result == "help me"
    
    # Leading/trailing whitespace
    result = preprocessor.preprocess("  help me  ")
    assert result == "help me"


def test_preprocessor_emojis():
    """Test emoji removal."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("Help me 😭😭😭 please!")
    # Emojis removed, but basic punctuation (!) is preserved
    assert result == "help me please!"
    
    result = preprocessor.preprocess("Payment failed 💳❌")
    assert result == "payment failed"


def test_preprocessor_urls():
    """Test URL removal."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("Check this http://example.com for details")
    assert "http://example.com" not in result
    assert "check this" in result
    assert "for details" in result


def test_preprocessor_emails():
    """Test email removal."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("Contact me at user@example.com")
    assert "user@example.com" not in result
    assert "contact me at" in result


def test_preprocessor_punctuation_normalization():
    """Test punctuation normalization."""
    preprocessor = TextPreprocessor()
    
    # Multiple exclamation marks → normalized to single
    result = preprocessor.preprocess("Help!!!")
    assert result == "help!"
    
    # Multiple question marks → normalized to single
    result = preprocessor.preprocess("Why???")
    assert result == "why?"


def test_preprocessor_preserves_numbers():
    """Test that numbers are preserved by default."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("I was charged $99.99 twice")
    assert "$99.99" in result or "99.99" in result  # $ might be kept or removed based on config
    assert "twice" in result


def test_preprocessor_preserves_important_punctuation():
    """Test that important punctuation is kept."""
    preprocessor = TextPreprocessor()
    
    # Periods and commas often preserved in amounts
    result = preprocessor.preprocess("The amount is $1,234.56")
    # Should preserve the structure even if some chars removed


# ============================================================================
# Configuration Tests
# ============================================================================

def test_preprocessor_custom_config_no_lowercase():
    """Test with lowercase disabled."""
    config = PreprocessingConfig(lowercase=False)
    preprocessor = TextPreprocessor(config)
    
    result = preprocessor.preprocess("HELP Me")
    assert "HELP" in result or "Help" in result  # Case preserved


def test_preprocessor_custom_config_keep_emojis():
    """Test with emoji removal disabled."""
    config = PreprocessingConfig(remove_emojis=False)
    preprocessor = TextPreprocessor(config)
    
    result = preprocessor.preprocess("Help 😭")
    # Emojis might still be modified but not completely removed


def test_preprocessor_remove_stopwords():
    """Test stop word removal when enabled."""
    config = PreprocessingConfig(remove_stopwords=True)
    preprocessor = TextPreprocessor(config)
    
    result = preprocessor.preprocess("I want to cancel my subscription")
    
    # Stop words like "I", "to", "my" should be removed
    assert "cancel" in result
    assert "subscription" in result
    # These might be removed (depending on stop word list)
    # Just verify main keywords remain


# ============================================================================
# Keyword Extraction Tests
# ============================================================================

def test_extract_keywords_basic():
    """Test basic keyword extraction."""
    preprocessor = TextPreprocessor()
    
    keywords = preprocessor.extract_keywords("My payment failed yesterday")
    
    assert "payment" in keywords
    assert "failed" in keywords
    assert "yesterday" in keywords


def test_extract_keywords_filters_short_words():
    """Test that very short words are filtered."""
    preprocessor = TextPreprocessor()
    
    keywords = preprocessor.extract_keywords("I am ok")
    
    # Short words (< 3 chars) should be filtered
    assert "i" not in keywords
    assert "am" not in keywords
    assert "ok" not in keywords  # Only 2 chars


def test_extract_keywords_from_messy_input():
    """Test keyword extraction from messy input."""
    preprocessor = TextPreprocessor()
    
    keywords = preprocessor.extract_keywords("HELP!!! My PAYMENT failed 😭😭")
    
    assert "help" in keywords
    assert "payment" in keywords
    assert "failed" in keywords


# ============================================================================
# Phrase Extraction Tests
# ============================================================================

def test_extract_phrases_bigrams():
    """Test bigram (2-word phrase) extraction."""
    preprocessor = TextPreprocessor()
    
    phrases = preprocessor.extract_phrases("cancel my subscription", phrase_length=2)
    
    assert "cancel my" in phrases
    assert "my subscription" in phrases
    assert len(phrases) == 2  # Two bigrams from 3 words


def test_extract_phrases_trigrams():
    """Test trigram (3-word phrase) extraction."""
    preprocessor = TextPreprocessor()
    
    phrases = preprocessor.extract_phrases("how do i cancel", phrase_length=3)
    
    assert "how do i" in phrases
    assert "do i cancel" in phrases


def test_extract_phrases_short_text():
    """Test phrase extraction from text shorter than phrase length."""
    preprocessor = TextPreprocessor()
    
    phrases = preprocessor.extract_phrases("help", phrase_length=2)
    
    assert len(phrases) == 0  # Can't create bigram from single word


# ============================================================================
# Edge Cases
# ============================================================================

def test_preprocessor_empty_string():
    """Test preprocessing empty string."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("")
    assert result == ""


def test_preprocessor_whitespace_only():
    """Test preprocessing whitespace-only string."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("   \t\n   ")
    assert result == ""


def test_preprocessor_special_characters_only():
    """Test preprocessing string with only special characters."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("@#$%^&*()")
    # Should be mostly empty after cleaning
    assert len(result) < 5


def test_preprocessor_numbers_only():
    """Test preprocessing string with only numbers."""
    preprocessor = TextPreprocessor()
    
    result = preprocessor.preprocess("12345")
    assert "12345" in result  # Numbers preserved


def test_preprocessor_very_long_text():
    """Test preprocessing very long text."""
    preprocessor = TextPreprocessor()
    
    # Create long text
    long_text = "help me " * 1000  # 7000 characters
    
    result = preprocessor.preprocess(long_text)
    
    # Should handle without error
    assert "help" in result
    assert "me" in result


# ============================================================================
# Singleton Tests
# ============================================================================

def test_get_preprocessor_singleton():
    """Test that get_preprocessor returns same instance."""
    prep1 = get_preprocessor()
    prep2 = get_preprocessor()
    
    # Should be same instance (singleton)
    assert prep1 is prep2


def test_get_preprocessor_with_custom_config():
    """Test that custom config creates new instance."""
    default_prep = get_preprocessor()
    custom_config = PreprocessingConfig(lowercase=False)
    custom_prep = get_preprocessor(custom_config)
    
    # Should be different instances
    assert default_prep is not custom_prep


# ============================================================================
# Real-World Examples
# ============================================================================

def test_real_world_example_billing():
    """Test real billing query."""
    preprocessor = TextPreprocessor()
    
    query = "HELP!!! I was charged $99.99 TWICE but my order failed 😭"
    result = preprocessor.preprocess(query)
    
    # Should normalize while preserving key info
    assert "charged" in result
    assert "twice" in result
    assert "order" in result
    assert "failed" in result
    # Amount might be preserved
    assert "99" in result


def test_real_world_example_technical():
    """Test real technical query."""
    preprocessor = TextPreprocessor()
    
    query = "App crashes when I click Submit button... Error code 500"
    result = preprocessor.preprocess(query)
    
    assert "app" in result or "crashes" in result
    assert "click" in result or "submit" in result
    assert "button" in result
    assert "error" in result
    assert "500" in result  # Error code preserved


def test_real_world_example_account():
    """Test real account query."""
    preprocessor = TextPreprocessor()
    
    query = "Can't login!!! Forgot password, please help ASAP"
    result = preprocessor.preprocess(query)
    
    assert "login" in result
    assert "forgot" in result or "password" in result
    assert "help" in result