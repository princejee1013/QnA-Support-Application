"""
Prompt templates for LLM classification.

This module contains carefully crafted prompts for Azure OpenAI
to classify support queries accurately.
"""

from typing import List
from src.core.config import get_settings


def get_classification_prompt(
    query: str,
    categories: List[str] = None
) -> str:
    """
    Generate classification prompt for LLM.
    
    Args:
        query: The support query to classify
        categories: List of valid categories (uses config if None)
        
    Returns:
        Formatted prompt string
    """
    settings = get_settings()
    
    if categories is None:
        categories = [
            "Billing & Payments",
            "Technical Issues",
            "Account Management",
            "Product Questions",
            "Feature Requests",
            "Bug Reports",
            "General Inquiry"
        ]
    
    categories_list = "\n".join([f"- {cat}" for cat in categories])
    
    prompt = f"""You are an expert customer support query classifier for a SaaS application.

Your task is to analyze the following customer support query and classify it into ONE category.

AVAILABLE CATEGORIES:
{categories_list}

CUSTOMER QUERY:
"{query}"

INSTRUCTIONS:
1. Read the query carefully and understand the customer's primary intent
2. Choose the MOST relevant category from the list above
3. Provide a confidence score between 0.0 and 1.0
4. Explain your reasoning in ONE concise sentence (max 100 characters)

CLASSIFICATION GUIDELINES:
- "Billing & Payments": Money, charges, refunds, subscriptions, invoices, payment methods
- "Technical Issues": Errors, crashes, bugs, performance problems, things not working
- "Account Management": Login, password, email, account settings, access issues
- "Product Questions": How-to questions, feature usage, general product inquiries
- "Feature Requests": Suggestions for new features or improvements
- "Bug Reports": Reports of incorrect behavior or unexpected results
- "General Inquiry": Greetings, general questions, unclear intent

IMPORTANT RULES:
- Be decisive - choose the PRIMARY category even if multiple could apply
- Use REALISTIC confidence scores based on query clarity:
  * 0.95-1.0: Extremely clear with explicit category keywords (rare)
  * 0.80-0.95: Very clear intent with strong indicators
  * 0.60-0.80: Clear but could fit multiple categories
  * 0.40-0.60: Ambiguous or lacks specific details
  * 0.20-0.40: Very vague or unclear intent
- Adjust confidence DOWN if the query is short, vague, or could fit multiple categories
- Never use exactly 0.9 - be more precise (e.g., 0.87, 0.76, 0.62)

SENTIMENT & URGENCY DETECTION:
- Detect customer emotion: frustrated, confused, angry, polite, urgent
- Note urgency indicators: "ASAP", "urgent", "immediately", multiple exclamation marks, all caps
- Include emotion/urgency in reasoning if detected

OUTPUT FORMAT (respond ONLY with valid JSON, no additional text):
{{
    "category": "Selected Category Name",
    "confidence": 0.75,
    "reasoning": "Brief explanation why this category",
    "sentiment": "frustrated",
    "urgency": "high"
}}

Respond now with ONLY the JSON object:"""
    
    return prompt


def get_validation_prompt(query: str, suggested_category: str) -> str:
    """
    Generate prompt to validate a rule-based classification.
    
    Used when rules have low confidence - asks LLM to verify.
    
    Args:
        query: The support query
        suggested_category: Category suggested by rules
        
    Returns:
        Validation prompt string
    """
    prompt = f"""You are validating a support query classification.

QUERY: "{query}"
SUGGESTED CATEGORY: "{suggested_category}"

Question: Is "{suggested_category}" the correct category for this query?

Respond with JSON only:
{{
    "is_correct": true,
    "confidence": 0.85,
    "alternative_category": "Different Category" or null,
    "reasoning": "Brief explanation"
}}"""
    
    return prompt


def get_multi_intent_prompt(query: str) -> str:
    """
    Generate prompt for detecting multiple intents in a query.
    
    Some queries have multiple issues - this helps identify all of them.
    
    Args:
        query: The support query
        
    Returns:
        Multi-intent detection prompt
    """
    prompt = f"""Analyze this support query for multiple intents/issues:

QUERY: "{query}"

Identify ALL distinct issues or questions in this query.

Respond with JSON only:
{{
    "has_multiple_intents": true,
    "primary_category": "Main Category",
    "secondary_categories": ["Other", "Categories"],
    "reasoning": "Explanation"
}}"""
    
    return prompt