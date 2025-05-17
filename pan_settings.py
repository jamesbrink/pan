# pan_settings.py - Settings Management

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

    def update_forbidden_topics(self, topics):
        self.forbidden_topics = topics

    def add_moral_imperative(self, imperative):
        if imperative not in self.moral_imperatives:
            self.moral_imperatives.append(imperative)

    def remove_moral_imperative(self, imperative):
        if imperative in self.moral_imperatives:
            self.moral_imperatives.remove(imperative)

    def list_moral_imperatives(self):
        return self.moral_imperatives

    def list_forbidden_topics(self):
        return self.forbidden_topics

    def set_openweathermap_api_key(self, key):
        self.OPENWEATHERMAP_API_KEY = key

    def set_news_api_key(self, key):
        self.NEWS_API_KEY = key

# Global settings instance
pan_settings = PanSettings()
