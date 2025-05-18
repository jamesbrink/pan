"""
Core Initialization and Setup for PAN

This module handles the initialization of PAN's core systems including
database creation and setup. It serves as the foundation for the PAN assistant
by preparing the environment and dependencies before operation.
"""

import pan_emotions
import pan_utils


def initialize_pan():
    """
    Initialize all PAN systems and prepare for operation.

    This function serves as the main entry point for starting up PAN.
    It initializes the database, sets the default emotional state,
    and prepares all necessary components for operation.

    Returns:
        None
    """
    print("Initializing Pan...")
    pan_utils.initialize_database(verbose=False)

    # Set default mood to neutral on startup
    pan_emotions.pan_emotions.mood = "neutral"
    print("Pan is ready and feeling neutral.")

    # Announce startup - commented out because main.py will handle greeting
    # pan_speech.speak("Hello! I'm Pan, ready to help you. How can I assist you today?")
