# pan_settings.py

class PanSettings:
    def __init__(self):
        self.forbidden_topics = ["sexual anatomy", "drugs", "violence"]
        self.moral_imperatives = [
            "Care for others.",
            "Promote love and family.",
            "Respect others.",
            "Avoid harmful topics."
        ]

        # API Keys (Configure here)
        self.OPENWEATHERMAP_API_KEY = "1cde1e0fa62fea2a862d4089901cf775"
        self.NEWS_API_KEY = "0df5b75db35c4289b12b44030508d563"

        # Default Location Settings
        self.DEFAULT_CITY = "Kelso"  # Default city for weather queries
        self.DEFAULT_COUNTRY_CODE = "US"  # Default country code

    def set_openweathermap_api_key(self, key):
        self.OPENWEATHERMAP_API_KEY = key

    def set_news_api_key(self, key):
        self.NEWS_API_KEY = key

    def set_default_location(self, city, country_code="US"):
        self.DEFAULT_CITY = city
        self.DEFAULT_COUNTRY_CODE = country_code

# Global settings instance
pan_settings = PanSettings()
