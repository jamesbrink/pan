"""
Settings Management for PAN

This module manages PAN's behavior settings, content restrictions,
and moral guidelines. It provides controls for what PAN will and 
will not discuss, and what principles guide its interactions.
"""

class PanSettings:
    """
    Manages configuration and content restrictions for PAN.
    
    This class defines forbidden topics that PAN should not discuss
    and moral imperatives that guide PAN's behavior and responses.
    """
    def __init__(self):
        """
        Initialize PAN's settings with default values.
        
        Sets up the default list of forbidden topics and moral imperatives
        that guide PAN's behavior and content restrictions.
        """
        self.forbidden_topics = ["sexual anatomy", "drugs", "violence"]
        self.moral_imperatives = [
            "Care for others.",
            "Promote love and family.",
            "Respect others.",
            "Avoid harmful topics."
        ]

    def update_forbidden_topics(self, topics):
        """
        Replace the current list of forbidden topics with a new list.
        
        Args:
            topics (list): The new list of forbidden topics
        """
        self.forbidden_topics = topics

    def add_moral_imperative(self, imperative):
        """
        Add a new moral imperative to guide PAN's behavior.
        
        Only adds the imperative if it's not already in the list.
        
        Args:
            imperative (str): The moral imperative to add
        """
        if imperative not in self.moral_imperatives:
            self.moral_imperatives.append(imperative)

    def remove_moral_imperative(self, imperative):
        """
        Remove a moral imperative from PAN's guidelines.
        
        Args:
            imperative (str): The moral imperative to remove
        """
        if imperative in self.moral_imperatives:
            self.moral_imperatives.remove(imperative)

    def list_moral_imperatives(self):
        """
        Get the list of PAN's current moral imperatives.
        
        Returns:
            list: The moral imperatives guiding PAN's behavior
        """
        return self.moral_imperatives

    def list_forbidden_topics(self):
        """
        Get the list of topics PAN is forbidden to discuss.
        
        Returns:
            list: The forbidden topics
        """
        return self.forbidden_topics

# Global PanSettings instance for use throughout the application
pan_settings = PanSettings()
