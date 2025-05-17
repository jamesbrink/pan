"""
Central Emotional Management for PAN

This module manages PAN's emotional state system. It tracks mood, adjusts responses
based on emotional state, and manages relationships with users through affinity scores.
The emotional system allows PAN to have a more human-like, nuanced personality.
"""


class PanEmotions:
    """
    Manages PAN's emotional state and relationship with users.

    This class provides functionality for adjusting, tracking, and responding based
    on different emotional states, as well as maintaining user relationships through
    affinity scores and favorite user tracking.
    """

    def __init__(self):
        """
        Initialize the PanEmotions instance with default values.

        Sets up the initial mood state, affinity thresholds for different moods,
        standard mood responses, and an empty set of favorite users.
        """
        self.mood = "neutral"
        self.affinity_thresholds = {"happy": 20, "neutral": 0, "sad": -10, "angry": -20}
        self.mood_responses = {
            "happy": "I'm feeling great today!",
            "neutral": "I'm feeling okay.",
            "sad": "I'm not feeling so good...",
            "angry": "I'm really upset right now.",
        }
        self.favorite_users = set()

    def adjust_mood(self, amount):
        """
        Adjust PAN's mood based on a numerical amount.

        Positive values make PAN happier, negative values make PAN sad or angry
        depending on the magnitude.

        Args:
            amount (int): The amount to adjust the mood by
        """
        if amount > 0:
            self.mood = (
                "happy" if amount > self.affinity_thresholds["happy"] else "neutral"
            )
        elif amount < 0:
            self.mood = "angry" if amount < self.affinity_thresholds["angry"] else "sad"
        else:
            self.mood = "neutral"

    def get_mood(self):
        """
        Return PAN's current mood state.

        Returns:
            str: The current mood ("happy", "neutral", "sad", or "angry")
        """
        return self.mood

    def react_to_affinity(self, affinity):
        """
        Set PAN's mood based on a user's affinity score.

        This allows PAN's emotional state to reflect the relationship
        quality with the current user.

        Args:
            affinity (int): The user's affinity score
        """
        if affinity > 20:
            self.mood = "happy"
        elif affinity < -20:
            self.mood = "angry"
        elif affinity < 0:
            self.mood = "sad"
        else:
            self.mood = "neutral"

    def respond_with_emotion(self, text):
        """
        Format a text response with an emoji based on the current mood.

        Adds an appropriate emoji to the beginning of the text to visually
        indicate PAN's current emotional state.

        Args:
            text (str): The text to format with emotion

        Returns:
            str: The emotionally formatted text
        """
        if self.mood == "happy":
            return f"😊 {text}"
        if self.mood == "sad":
            return f"😟 {text}"
        if self.mood == "angry":
            return f"😡 {text}"
        return text

    def express_feelings(self):
        """
        Return a sentence expressing PAN's current feelings.

        Useful for when PAN needs to directly communicate its emotional state.

        Returns:
            str: A sentence describing PAN's current mood
        """
        return self.mood_responses.get(self.mood, "I'm not sure how I feel.")

    def manage_favorite_users(self, user_id, affinity):
        """
        Update PAN's list of favorite users based on affinity scores.

        Adds users with high affinity to favorites, and removes users
        whose affinity drops below a threshold.

        Args:
            user_id (str): The ID of the user to evaluate
            affinity (int): The user's current affinity score
        """
        if affinity > 30:
            self.favorite_users.add(user_id)
        elif user_id in self.favorite_users and affinity < 10:
            self.favorite_users.remove(user_id)

    def list_favorites(self):
        """
        Get a list of PAN's favorite users as a formatted string.

        Returns:
            str: A string describing PAN's favorite users, or indicating that
                 there are none yet
        """
        if self.favorite_users:
            return f"I've grown really fond of: {', '.join(self.favorite_users)}"
        return "I don't have any favorite people yet."


# Global PanEmotions instance for use throughout the application
pan_emotions = PanEmotions()
