"""
Settings Management for PAN

This module manages PAN's behavior settings, content restrictions,
and moral guidelines. It provides controls for what PAN will and 
will not discuss, and what principles guide its interactions.
"""

class PanSettings:
    """
    Manages configuration and content restrictions for PAN.
    """

    def __init__(self):
        self.forbidden_topics = ["sexual anatomy", "drugs", "violence"]
        self.moral_imperatives = [
            "Care for others.",
            "Promote love and family.",
            "Respect others.",
            "Avoid harmful topics."
        ]
        # API Keys (Configure here)
        self.OPENWEATHERMAP_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
        self.NEWS_API_KEY = "YOUR_NEWS_API_KEY"

    def set_openweathermap_api_key(self, key):
        self.OPENWEATHERMAP_API_KEY = key

    def set_news_api_key(self, key):
        self.NEWS_API_KEY = key

# Global settings instance
pan_settings = PanSettings()
