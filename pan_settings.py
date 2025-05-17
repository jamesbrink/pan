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

pan_settings = PanSettings()
