"""
Configuration Management for PAN

This module loads and manages configuration settings from environment variables,
with sensible defaults for development. It uses python-dotenv to load variables
from a .env file if present.
"""

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

# Set TOKENIZERS_PARALLELISM environment variable to suppress warnings
os.environ["TOKENIZERS_PARALLELISM"] = os.getenv("TOKENIZERS_PARALLELISM", "false")

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("Warning: .env file not found. Using default settings.")

# Database settings
DATABASE_PATH = os.getenv("DATABASE_PATH", "pan_memory.db")

# API keys (Weather and News)
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not OPENWEATHERMAP_API_KEY:
    print("Warning: Weather API key is missing. Weather functionality will be limited.")

if not NEWS_API_KEY:
    print("Warning: News API key is missing. News functionality will be limited.")

# AI model settings
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt2")
CONVERSATION_MODEL_NAME = os.getenv("CONVERSATION_MODEL_NAME", "EleutherAI/gpt-j-6B")
MAX_MEMORY_LENGTH = int(os.getenv("MAX_MEMORY_LENGTH", "10"))
MODEL_CONTEXT_LENGTH = int(os.getenv("MODEL_CONTEXT_LENGTH", "2048"))
MODEL_QUANTIZATION_LEVEL = os.getenv("MODEL_QUANTIZATION_LEVEL", "4bit")

# Location settings
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Kelso")
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "US")

# Assistant settings
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Pan")

# Voice settings
DEFAULT_VOICE_RATE = int(os.getenv("DEFAULT_VOICE_RATE", "160"))
DEFAULT_VOICE_VOLUME = float(os.getenv("DEFAULT_VOICE_VOLUME", "0.9"))

# Platform-specific voice settings
if platform.system() == "Darwin":
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

# Keyword detection settings
USE_KEYWORD_ACTIVATION = os.getenv("USE_KEYWORD_ACTIVATION", "True").lower() == "true"
KEYWORD_ACTIVATION_THRESHOLD = float(os.getenv("KEYWORD_ACTIVATION_THRESHOLD", "0.6"))
CONTINUOUS_LISTENING = os.getenv("CONTINUOUS_LISTENING", "True").lower() == "true"


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
            "weather": OPENWEATHERMAP_API_KEY or "Not Set",
            "news": NEWS_API_KEY or "Not Set",
        },
        "location": {
            "city": DEFAULT_CITY,
            "country_code": DEFAULT_COUNTRY_CODE,
        },
        "assistant": {
            "name": ASSISTANT_NAME,
        },
        "ai": {
            "model_name": LLM_MODEL_NAME,
            "conversation_model": CONVERSATION_MODEL_NAME,
            "max_memory_length": MAX_MEMORY_LENGTH,
            "context_length": MODEL_CONTEXT_LENGTH,
            "quantization_level": MODEL_QUANTIZATION_LEVEL,
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
            "use_keyword_activation": USE_KEYWORD_ACTIVATION,
            "keyword_activation_threshold": KEYWORD_ACTIVATION_THRESHOLD,
            "continuous_listening": CONTINUOUS_LISTENING,
        },
    }


# Display configuration on startup (for debugging)
if __name__ == "__main__":
    print("Loaded Configuration:")
    for key, value in get_config().items():
        print(f"{key}: {value}")
