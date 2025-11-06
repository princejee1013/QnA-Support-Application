"""
Configuration verification script.

Run this to check if your .env file is correctly configured.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_settings
from pydantic import ValidationError


def verify_configuration():
    """Verify all configuration settings."""
    print("=" * 60)
    print("🔍 CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    try:
        settings = get_settings()
        
        print("\n✅ Configuration loaded successfully!\n")
        
        # Azure OpenAI Settings
        print("📱 AZURE OPENAI CONFIGURATION:")
        print(f"   Endpoint: {settings.azure_openai_endpoint}")
        print(f"   API Version: {settings.azure_openai_api_version}")
        print(f"   Deployment: {settings.azure_openai_deployment_name}")
        print(f"   Model: {settings.azure_openai_model_name}")
        print(f"   API Key: {'*' * 20}{settings.azure_openai_api_key[-4:]}")  # Show last 4 chars
        
        # Application Settings
        print(f"\n⚙️  APPLICATION SETTINGS:")
        print(f"   Confidence Threshold: {settings.confidence_threshold}")
        print(f"   Max Tokens: {settings.max_tokens}")
        print(f"   Temperature: {settings.temperature}")
        
        # Logging
        print(f"\n📝 LOGGING:")
        print(f"   Log Level: {settings.log_level}")
        print(f"   Retention: {settings.log_retention_days} days")
        
        # App Info
        print(f"\n📦 APPLICATION:")
        print(f"   Name: {settings.app_name}")
        print(f"   Version: {settings.app_version}")
        
        print("\n" + "=" * 60)
        print("✅ All settings valid and ready to use!")
        print("=" * 60)
        
        return True
        
    except ValidationError as e:
        print("\n❌ CONFIGURATION ERROR!\n")
        print(e)
        print("\n💡 Fix your .env file and try again.")
        return False
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    verify_configuration()