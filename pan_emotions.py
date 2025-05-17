# pan_emotions.py - Central Emotional Management for Pan

class PanEmotions:
    def __init__(self):
        self.mood = "neutral"
        self.affinity_thresholds = {
            'happy': 20,
            'neutral': 0,
            'sad': -10,
            'angry': -20
        }
        self.mood_responses = {
            'happy': "I'm feeling great today!",
            'neutral': "I'm feeling okay.",
            'sad': "I'm not feeling so good...",
            'angry': "I'm really upset right now."
        }
        self.favorite_users = set()

    def adjust_mood(self, amount):
        if amount > 0:
            self.mood = "happy" if amount > self.affinity_thresholds['happy'] else "neutral"
        elif amount < 0:
            self.mood = "angry" if amount < self.affinity_thresholds['angry'] else "sad"
        else:
            self.mood = "neutral"

    def get_mood(self):
        return self.mood

    def react_to_affinity(self, affinity):
        if affinity > 20:
            self.mood = "happy"
        elif affinity < -20:
            self.mood = "angry"
        elif affinity < 0:
            self.mood = "sad"
        else:
            self.mood = "neutral"

    def respond_with_emotion(self, text):
        if self.mood == "happy":
            return f"😊 {text}"
        elif self.mood == "sad":
            return f"😟 {text}"
        elif self.mood == "angry":
            return f"😡 {text}"
        return text

    def express_feelings(self):
        return self.mood_responses.get(self.mood, "I'm not sure how I feel.")

    def manage_favorite_users(self, user_id, affinity):
        if affinity > 30:
            self.favorite_users.add(user_id)
        elif user_id in self.favorite_users and affinity < 10:
            self.favorite_users.remove(user_id)

    def list_favorites(self):
        if self.favorite_users:
            return f"I've grown really fond of: {', '.join(self.favorite_users)}"
        else:
            return "I don't have any favorite people yet."

# Global PanEmotions instance
pan_emotions = PanEmotions()
