"""
PAN - Personal Assistant with Nuance

Main entry point for the PAN digital assistant. Handles initialization,
user interaction, command processing, and manages the autonomous curiosity system.
"""

import random
import threading
import time
from datetime import datetime

import pan_config  # Centralized Configuration
import pan_conversation
import pan_core
import pan_research
import pan_speech


# App state management class
class PanState:
    """Class to manage PAN application state"""

    # State variables
    curiosity_active = True
    last_interaction_time = time.time()
    last_speech_time = 0

    # Configuration settings with defaults
    MAX_SHORT_TERM_MEMORY = 10
    IDLE_THRESHOLD_SECONDS = 300  # 5 minutes
    MIN_SPEECH_INTERVAL_SECONDS = 15

    @classmethod
    def load_config(cls):
        """Load configuration settings from config module"""
        config = pan_config.get_config()
        cls.MAX_SHORT_TERM_MEMORY = config["conversation"]["max_short_term_memory"]
        cls.IDLE_THRESHOLD_SECONDS = config["conversation"]["idle_threshold_seconds"]
        cls.MIN_SPEECH_INTERVAL_SECONDS = config["conversation"][
            "min_speech_interval_seconds"
        ]


# Initialize configuration
PanState.load_config()


def check_macos_microphone_permissions():
    """
    Check microphone permissions on macOS.

    Displays an error message if microphones are not detected or
    permissions are denied. This function should be called on startup
    when running on macOS.
    """
    import platform

    import speech_recognition as sr

    if platform.system() != "Darwin":
        # Not macOS, no need to check
        return

    try:
        # Try to list available microphones
        microphones = sr.Microphone.list_microphone_names()
        if not microphones:
            print("\n" + "=" * 50)
            print("MACOS MICROPHONE PERMISSION ALERT")
            print("=" * 50)
            print("No microphones were detected on your Mac.")
            print("Please check your microphone connections.")
            print("If using a built-in microphone, make sure permissions are enabled:")
            print("System Settings → Privacy & Security → Microphone")
            print("=" * 50 + "\n")
    except OSError as e:
        print("\n" + "=" * 50)
        print("MACOS MICROPHONE PERMISSION ERROR")
        print("=" * 50)
        print(f"Error accessing microphone: {e}")
        print("Please enable microphone permissions:")
        print("System Settings → Privacy & Security → Microphone")
        print("=" * 50 + "\n")


def get_time_based_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning!"
    if 12 <= hour < 17:
        return "Good afternoon!"
    if 17 <= hour < 22:
        return "Good evening!"
    return "Hello!"


def curiosity_loop():
    """Background thread to periodically perform curiosity actions when idle"""

    while PanState.curiosity_active:
        time.sleep(10)
        idle_time = time.time() - PanState.last_interaction_time

        if idle_time >= PanState.IDLE_THRESHOLD_SECONDS:
            topic = random.choice(["space", "history", "technology", "science"])
            search_result = pan_research.live_search(topic)
            pan_speech.speak(
                f"I just learned something amazing about {topic}! {search_result}"
            )

            # Update timestamps
            PanState.last_speech_time = time.time()
            PanState.last_interaction_time = time.time()


def listen_with_retries(max_attempts=3, timeout=5):
    for attempt in range(max_attempts):
        text = pan_speech.listen_to_user(timeout=timeout)
        if text:
            return text
        print(f"Listen attempt {attempt + 1} failed, retrying...")
        time.sleep(1)
    return None


if __name__ == "__main__":
    print("Pan is starting...")
    pan_core.initialize_pan()
    greeting = get_time_based_greeting()
    pan_speech.speak(
        f"{greeting} I'm Pan, ready to help you. How can I assist you today?"
    )

    curiosity_thread = threading.Thread(target=curiosity_loop, daemon=True)
    curiosity_thread.start()

    user_id = "default_user"

    while True:
        user_input = listen_with_retries()
        if user_input:
            user_input_lower = user_input.lower()

            if "exit program" in user_input_lower:
                pan_speech.speak("Goodbye! Shutting down now.")
                PanState.curiosity_active = False
                curiosity_thread.join(timeout=5)
                break

            # Update interaction time
            PanState.last_interaction_time = time.time()

            # Process the user input
            response = pan_conversation.respond(user_input, user_id)

            print(f"Pan: {response}")
            pan_speech.speak(response)
        else:
            print("No valid input detected, listening again...")
