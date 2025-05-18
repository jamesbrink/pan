import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PanSettings:
    def __init__(self):
        self.forbidden_topics = ["sexual anatomy", "drugs", "violence"]
        self.moral_imperatives = [
            "Care for others.",
            "Promote love and family.",
            "Respect others.",
            "Avoid harmful topics.",
        ]

        # API Keys (Loaded from .env)
        self.OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")

        # Default Location Settings (Loaded from .env)
        self.DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Kelso")
        self.DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "US")

        # Conversation Mode (Advanced LLM)
        self.USE_GPT2_FOR_CONVERSATION = (
            True  # Set to False to disable advanced conversation
        )

    def set_openweathermap_api_key(self, key):
        self.OPENWEATHERMAP_API_KEY = key

    def set_news_api_key(self, key):
        self.NEWS_API_KEY = key


# Global settings instance
pan_settings = PanSettings()
