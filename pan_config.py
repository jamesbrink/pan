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

# Assistant settings
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Pan")

# Voice settings
DEFAULT_VOICE_RATE = int(os.getenv("DEFAULT_VOICE_RATE", "160"))
DEFAULT_VOICE_VOLUME = float(os.getenv("DEFAULT_VOICE_VOLUME", "0.9"))

# Platform-specific voice settings
import platform
if platform.system() == 'Darwin':
    # macOS typically needs a higher rate for NSSpeechSynthesizer
    DEFAULT_VOICE_RATE = int(os.getenv("MACOS_VOICE_RATE", "190"))

# Conversation settings
MAX_SHORT_TERM_MEMORY = int(os.getenv("MAX_SHORT_TERM_MEMORY", "10"))
IDLE_THRESHOLD_SECONDS = int(os.getenv("IDLE_THRESHOLD_SECONDS", "300"))
MIN_SPEECH_INTERVAL_SECONDS = int(os.getenv("MIN_SPEECH_INTERVAL_SECONDS", "15"))

# Speech recognition settings
AMBIENT_NOISE_DURATION = float(os.getenv("AMBIENT_NOISE_DURATION", "3.0"))
USE_DYNAMIC_ENERGY_THRESHOLD = (
    os.getenv("USE_DYNAMIC_ENERGY_THRESHOLD", "True").lower() == "true"
)
ENERGY_THRESHOLD = int(os.getenv("ENERGY_THRESHOLD", "300"))
SPEECH_RECOGNITION_TIMEOUT = int(os.getenv("SPEECH_RECOGNITION_TIMEOUT", "5"))
PHRASE_TIME_LIMIT = int(os.getenv("PHRASE_TIME_LIMIT", "10"))

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
        "assistant": {
            "name": ASSISTANT_NAME,
        },
        "voice": {
            "rate": DEFAULT_VOICE_RATE,
            "volume": DEFAULT_VOICE_VOLUME,
        },
        "conversation": {
            "max_short_term_memory": MAX_SHORT_TERM_MEMORY,
            "idle_threshold_seconds": IDLE_THRESHOLD_SECONDS,
            "min_speech_interval_seconds": MIN_SPEECH_INTERVAL_SECONDS,
        },
        "speech_recognition": {
            "ambient_noise_duration": AMBIENT_NOISE_DURATION,
            "use_dynamic_energy_threshold": USE_DYNAMIC_ENERGY_THRESHOLD,
            "energy_threshold": ENERGY_THRESHOLD,
            "speech_recognition_timeout": SPEECH_RECOGNITION_TIMEOUT,
            "phrase_time_limit": PHRASE_TIME_LIMIT,
        }
    }

# Display configuration on startup (for debugging)
if __name__ == "__main__":
    print("Loaded Configuration:")
    for key, value in get_config().items():
        print(f"{key}: {value}")
