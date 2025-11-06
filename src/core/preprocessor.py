"""
Text preprocessing for support query classification.

This module provides text cleaning and normalization while preserving
information important for classification (amounts, dates, context).

Philosophy:
- Normalize for consistent matching (lowercase, whitespace)
- Preserve information for reasoning (numbers, basic punctuation)
- Keep it readable for debugging and user feedback
"""

import re
import unicodedata
from typing import List, Set
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger()


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PreprocessingConfig:
    """
    Configuration for text preprocessing.
    
    Allows customization of preprocessing behavior.
    """
    
    # Core operations
    lowercase: bool = True
    strip_whitespace: bool = True
    normalize_whitespace: bool = True
    
    # Character handling
    remove_emojis: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    
    # Punctuation
    normalize_punctuation: bool = True  # Multiple !!! → single !
    remove_extra_punctuation: bool = True  # Keep only . ! ? , ;
    
    # Numbers (usually keep them!)
    remove_numbers: bool = False  # Keep $99, dates, etc.
    
    # Advanced (usually False for our use case)
    remove_stopwords: bool = False
    apply_stemming: bool = False
    
    # Minimum length after processing
    min_length: int = 3




# ============================================================================
# PREPROCESSOR CLASS
# ============================================================================

class TextPreprocessor:
    """
    Text preprocessor for support queries.
    
    Cleans and normalizes text while preserving important information.
    """
    
    def __init__(self, config: PreprocessingConfig = None):
        """
        Initialize preprocessor.
        
        Args:
            config: Preprocessing configuration (uses defaults if None)
        """
        self.config = config or PreprocessingConfig()
        
        # Compile regex patterns once (performance optimization)
        self._compile_patterns()
        
        # Common English stop words (only if needed)
        self._stop_words = self._load_stop_words()
        
        logger.debug("TextPreprocessor initialized", config=self.config)
    
    def _compile_patterns(self):
        """Compile regex patterns for reuse (performance)."""
        
        # URL pattern
        self._url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Email pattern
        self._email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Multiple punctuation (!!!, ???, ...)
        self._multi_punct_pattern = re.compile(r'([!?.]){2,}')
        
        # Multiple spaces/tabs/newlines
        self._whitespace_pattern = re.compile(r'\s+')
        
        # Special characters to remove (keep alphanumeric, basic punctuation, $)
        self._special_chars_pattern = re.compile(r'[^a-zA-Z0-9\s.,!?;:$\-]')
    
    def _load_stop_words(self) -> Set[str]:
        """
        Load common stop words.
        
        Note: We rarely remove these for support queries,
        but available if needed.
        """
        return {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
            'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
            'against', 'between', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in',
            'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once'
        }
    
    def preprocess(self, text: str) -> str:
        """
        Main preprocessing pipeline.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned and normalized text
            
        Example:
            >>> preprocessor = TextPreprocessor()
            >>> preprocessor.preprocess("HELP!!! My payment FAILED 😭")
            'help my payment failed'
        """
        if not text or not text.strip():
            logger.warning("Empty text received for preprocessing")
            return ""
        
        original_text = text
        logger.debug("Preprocessing text", original_length=len(text))
        
        # Step 1: Remove URLs (before other processing)
        if self.config.remove_urls:
            text = self._remove_urls(text)
        
        # Step 2: Remove emails
        if self.config.remove_emails:
            text = self._remove_emails(text)
        
        # Step 3: Remove emojis and special Unicode
        if self.config.remove_emojis:
            text = self._remove_emojis(text)
        
        # Step 4: Normalize punctuation
        if self.config.normalize_punctuation:
            text = self._normalize_punctuation(text)
        
        # Step 5: Remove extra special characters
        if self.config.remove_extra_punctuation:
            text = self._remove_special_characters(text)
        
        # Step 6: Lowercase
        if self.config.lowercase:
            text = text.lower()
        
        # Step 7: Normalize whitespace
        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # Step 8: Strip leading/trailing whitespace
        if self.config.strip_whitespace:
            text = text.strip()
        
        # Step 9: Remove stop words (optional, usually False)
        if self.config.remove_stopwords:
            text = self._remove_stopwords(text)
        
        # Validation
        if len(text) < self.config.min_length:
            logger.warning(
                "Text too short after preprocessing",
                original=original_text,
                processed=text,
                length=len(text)
            )
        
        logger.debug(
            "Preprocessing complete",
            original_length=len(original_text),
            processed_length=len(text)
        )
        
        return text
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        return self._url_pattern.sub(' ', text)
    
    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        return self._email_pattern.sub(' ', text)
    
    def _remove_emojis(self, text: str) -> str:
        """
        Remove emojis and other special Unicode characters.
        
        Keeps ASCII characters, basic Latin, and common symbols.
        """
        # Keep ASCII printable characters and spaces
        cleaned = []
        for char in text:
            # Keep if:
            # - ASCII alphanumeric or punctuation
            # - Or common currency symbols
            if (ord(char) < 128 or  # ASCII
                char in {'$', '€', '£', '¥'}):  # Currency
                cleaned.append(char)
            else:
                # Replace emoji/Unicode with space
                cleaned.append(' ')
        
        return ''.join(cleaned)
    
    def _normalize_punctuation(self, text: str) -> str:
        """
        Normalize repeated punctuation.
        
        Examples:
            "Help!!!" → "Help!"
            "Really???" → "Really?"
            "Wait..." → "Wait."
        """
        # Replace multiple punctuation with single
        text = self._multi_punct_pattern.sub(r'\1', text)
        return text
    
    def _remove_special_characters(self, text: str) -> str:
        """
        Remove special characters while keeping important ones.
        
        Keeps:
        - Alphanumeric (a-z, A-Z, 0-9)
        - Basic punctuation (. , ! ? ; :)
        - Dollar sign ($)
        - Hyphen (-)
        - Spaces
        """
        return self._special_chars_pattern.sub(' ', text)
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize all whitespace to single spaces.
        
        Replaces tabs, newlines, multiple spaces with single space.
        """
        return self._whitespace_pattern.sub(' ', text)
    
    def _remove_stopwords(self, text: str) -> str:
        """
        Remove common stop words.
        
        Note: Usually NOT recommended for support queries as it
        loses context. Use sparingly.
        """
        words = text.split()
        filtered_words = [w for w in words if w not in self._stop_words]
        return ' '.join(filtered_words)
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text.
        
        This preprocesses text and returns individual words
        (excluding very short words).
        
        Args:
            text: Input text
            
        Returns:
            List of keywords (punctuation stripped)
            
        Example:
            >>> preprocessor.extract_keywords("My payment failed!")
            ['payment', 'failed']
        """
        # Preprocess first
        cleaned = self.preprocess(text)
        
        # Split into words
        words = cleaned.split()
        
        # Strip punctuation from each word and filter out very short words
        keywords = []
        for word in words:
            # Remove trailing/leading punctuation
            word = word.strip('.,!?;:-')
            # Keep if longer than 2 chars
            if len(word) > 2:
                keywords.append(word)
        
        logger.debug("Extracted keywords", count=len(keywords), keywords=keywords[:10])
        
        return keywords
    
    def extract_phrases(self, text: str, phrase_length: int = 2) -> List[str]:
        """
        Extract n-grams (phrases) from text.
        
        Useful for matching multi-word patterns like "refund request".
        
        Args:
            text: Input text
            phrase_length: Length of phrases (2 = bigrams, 3 = trigrams)
            
        Returns:
            List of phrases
            
        Example:
            >>> preprocessor.extract_phrases("cancel my subscription", 2)
            ['cancel my', 'my subscription']
        """
        cleaned = self.preprocess(text)
        words = cleaned.split()
        
        if len(words) < phrase_length:
            return []
        
        phrases = []
        for i in range(len(words) - phrase_length + 1):
            phrase = ' '.join(words[i:i + phrase_length])
            phrases.append(phrase)
        
        return phrases


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

# Global default preprocessor instance (singleton pattern)
_default_preprocessor = None

def get_preprocessor(config: PreprocessingConfig = None) -> TextPreprocessor:
    """
    Get preprocessor instance (singleton).
    
    Args:
        config: Custom configuration (creates new instance if provided)
        
    Returns:
        TextPreprocessor instance
    """
    global _default_preprocessor
    
    if config is not None:
        # Custom config requested, return new instance
        return TextPreprocessor(config)
    
    # Use cached default instance
    if _default_preprocessor is None:
        _default_preprocessor = TextPreprocessor()
    
    return _default_preprocessor