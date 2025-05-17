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
        self.DEFAULT_CITY = "Kelso"
        self.DEFAULT_COUNTRY_CODE = "US"

        # Conversation Mode (Advanced GPT-2)
        self.USE_GPT2_FOR_CONVERSATION = True  # Set to False to disable GPT-2

    def set_use_gpt2(self, enabled: bool):
        self.USE_GPT2_FOR_CONVERSATION = enabled

# Global settings instance
pan_settings = PanSettings()
