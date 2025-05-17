"""
Configuration Management for PAN

This module loads and manages configuration settings from environment variables,
with sensible defaults for development. It uses python-dotenv to load variables
from a .env file if present.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("Warning: .env file not found. Using default settings.")

# Database settings
DATABASE_PATH = os.getenv("DATABASE_PATH", "pan_memory.db")

# API keys (Weather and News)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not WEATHER_API_KEY:
    print("Warning: Weather API key is missing. Weather functionality will be limited.")

if not NEWS_API_KEY:
    print("Warning: News API key is missing. News functionality will be limited.")

# Location settings
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Kelso")
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "US")

# Voice settings
DEFAULT_VOICE_RATE = int(os.getenv("DEFAULT_VOICE_RATE", "160"))
DEFAULT_VOICE_VOLUME = float(os.getenv("DEFAULT_VOICE_VOLUME", "0.9"))

# Conversation settings
MAX_SHORT_TERM_MEMORY = int(os.getenv("MAX_SHORT_TERM_MEMORY", "10"))
IDLE_THRESHOLD_SECONDS = int(os.getenv("IDLE_THRESHOLD_SECONDS", "300"))
MIN_SPEECH_INTERVAL_SECONDS = int(os.getenv("MIN_SPEECH_INTERVAL_SECONDS", "15"))

def get_config():
    """
    Return all configuration settings as a dictionary.
    
    Returns:
        dict: All configuration settings
    """
    return {
        "database": {
            "path": DATABASE_PATH,
        },
        "api_keys": {
            "weather": WEATHER_API_KEY or "Not Set",
            "news": NEWS_API_KEY or "Not Set",
        },
        "location": {
            "city": DEFAULT_CITY,
            "country_code": DEFAULT_COUNTRY_CODE,
        },
        "voice": {
            "rate": DEFAULT_VOICE_RATE,
            "volume": DEFAULT_VOICE_VOLUME,
        },
        "conversation": {
            "max_short_term_memory": MAX_SHORT_TERM_MEMORY,
            "idle_threshold_seconds": IDLE_THRESHOLD_SECONDS,
            "min_speech_interval_seconds": MIN_SPEECH_INTERVAL_SECONDS,
        }
    }

# Display configuration on startup (for debugging)
if __name__ == "__main__":
    print("Loaded Configuration:")
    for key, value in get_config().items():
        print(f"{key}: {value}")
