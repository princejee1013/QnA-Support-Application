"""
Configuration management for QnA Support Application.

This module handles all application settings, loading from environment
variables with validation and type safety.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are loaded from .env file and validated at startup.
    If validation fails, the application won't start - fail fast!
    """
    
    
    # AZURE OPENAI CONFIGURATION
    
    azure_openai_api_key: str = Field(
        description="Azure OpenAI API key from Azure Portal",
        min_length=10  # Basic validation - real keys are longer
    )
    
    azure_openai_endpoint: str = Field(
        description="Azure OpenAI endpoint URL",
        pattern=r"^https://.*\.openai\.azure\.com.*$"  # Must be valid Azure URL (with or without path)
    )
    
    azure_openai_api_version: str = Field(
        default="2025-01-01-preview",
        description="Azure OpenAI API version"
    )
    
    azure_openai_deployment_name: str = Field(
        description="Deployment name from Azure OpenAI Studio",
        min_length=1
    )
    
    azure_openai_model_name: str = Field(
        default="gpt-4o-mini",
        description="Underlying model name"
    )
    
    
    # APPLICATION SETTINGS
   
    
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,  # Greater than or equal to 0
        le=1.0,  # Less than or equal to 1
        description="Minimum confidence to accept rule-based classification"
    )
    
    max_tokens: int = Field(
        default=150,
        ge=1,
        le=4000,
        description="Maximum tokens in LLM response"
    )
    
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0=deterministic, 2=creative)"
    )
    
    
    # LOGGING CONFIGURATION
    
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    log_retention_days: int = Field(
        default=7,
        ge=1,
        description="How many days to keep log files"
    )
    
    # ============================================================================
    # APP METADATA
    # ============================================================================
    
    app_name: str = Field(
        default="QnA Support Application",
        description="Application name"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    
    # PYDANTIC CONFIGURATION
    
    
    model_config = SettingsConfigDict(
        env_file=".env",              # Load from .env file
        env_file_encoding="utf-8",    # Handle special characters
        case_sensitive=False,         # AZURE_OPENAI_API_KEY = azure_openai_api_key
        extra="ignore"                # Ignore extra vars in .env (don't crash)
    )

        
    
    # CUSTOM VALIDATORS
  
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        
        if v_upper not in allowed_levels:
            raise ValueError(
                f"log_level must be one of {allowed_levels}, got '{v}'"
            )
        
        return v_upper  # Always return uppercase
    
    @field_validator('azure_openai_endpoint')
    @classmethod
    def validate_endpoint_format(cls, v: str) -> str:
        """Ensure endpoint doesn't have trailing slashes issues."""
        # Remove trailing slash for consistency
        return v.rstrip('/')
    



# SINGLETON PATTERN - CRITICAL FOR PERFORMANCE


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached singleton).
    
    This function is called throughout the application but only
    loads/validates settings ONCE, then returns the cached instance.
    
    Returns:
        Settings: Validated application settings
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.azure_openai_endpoint)
        https://my-resource.openai.azure.com
    """
    return Settings()



# CONVENIENCE: Create a global instance for imports


settings = get_settings()