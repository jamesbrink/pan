"""
PAN - Personal Assistant with Nuance

Main entry point for the PAN digital assistant. Handles initialization,
user interaction, command processing, and manages the autonomous curiosity system.
"""

import random
import sys
import threading
import time
from datetime import datetime

import pan_config
import pan_conversation
import pan_core
import pan_memory
import pan_research
import pan_speech

# Global variables for tracking state
curiosity_active = True
last_interaction_time = time.time()
last_speech_time = 0
MIN_SPEECH_INTERVAL = pan_config.MIN_SPEECH_INTERVAL_SECONDS


def get_time_based_greeting():
    """
    Generate a time-appropriate greeting based on the current hour.

    Returns:
        str: A greeting appropriate for the current time of day
    """
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning!"
    if 12 <= hour < 17:
        return "Good afternoon!"
    if 17 <= hour < 22:
        return "Good evening!"
    return "Hello!"


def curiosity_loop():
    """
    Background thread function that manages PAN's autonomous research behavior.

    When PAN is idle for a specified time, it will autonomously research random topics
    and share what it learns. This creates a more lifelike, curious personality.

    Global variables:
        last_interaction_time: Time of the most recent user interaction
        last_speech_time: Time of the most recent speech output
        curiosity_active: Controls whether this loop continues running
    """
    # We need to access the global variables to update them
    global last_interaction_time, last_speech_time
    idle_threshold = pan_config.IDLE_THRESHOLD_SECONDS

    while curiosity_active:
        time.sleep(10)  # Check every 10 seconds

        idle_time = time.time() - last_interaction_time
        if idle_time >= idle_threshold:
            now = time.time()
            if now - last_speech_time >= MIN_SPEECH_INTERVAL:
                research_topic = random.choice(["space", "history", "technology", "science"])
                print(f"Pan is curious about {research_topic}...")
                pan_speech.speak(
                    f"I'm curious about {research_topic}. Let me see what I can find.",
                    mood_override="curious",
                )

                search_response = pan_research.live_search(research_topic)
                pan_memory.remember(research_topic, search_response)
                print(f"Pan's curiosity: {search_response}")

                pan_speech.speak(
                    f"I just learned something amazing about {research_topic}! Did you know? {search_response}"
                )

                last_speech_time = now
                last_interaction_time = now
            else:
                print("Skipping curiosity speech to avoid overlap")


def listen_with_retries(max_attempts=3, timeout=5):
    """
    Attempt to listen for user speech input with multiple retries on failure.

    This function ensures that PAN waits for any text-to-speech to finish before
    attempting to listen, and retries listening if no clear speech is detected.

    Args:
        max_attempts (int): Maximum number of listening attempts before giving up
        timeout (int): Maximum time in seconds to wait for speech input on each attempt

    Returns:
        str or None: Transcribed speech text if successful, None if all attempts fail

    Raises:
        KeyboardInterrupt: Re-raises keyboard interrupt to allow clean exit
    """
    for attempt in range(max_attempts):
        wait_start = time.time()
        wait_timeout = 30  # seconds
        last_log_time = 0

        # Wait for TTS to finish speaking before listening
        while pan_speech.speak_manager.speaking_event.is_set():
            elapsed = time.time() - wait_start
            if elapsed > wait_timeout:
                print(
                    f"Warning: Timeout waiting for TTS to finish ({elapsed:.1f}s), forcing listen."
                )
                break
            if int(elapsed) % 5 == 0 and int(elapsed) != last_log_time:
                print(
                    f"Still waiting for TTS to finish after {int(elapsed)} seconds..."
                )
                last_log_time = int(elapsed)
            time.sleep(0.1)

        try:
            text = pan_speech.listen_to_user(timeout=timeout)
            if text:
                return text
            print(f"Listen attempt {attempt + 1} failed, retrying...")
            time.sleep(1)
        except KeyboardInterrupt:
            # Re-raise the keyboard interrupt to ensure it's caught by the main try/except
            print("\nKeyboard interrupt detected during listening...")
            raise

    print("Max listen attempts reached without success.")
    return None


if __name__ == "__main__":
    try:
        print("Pan is starting...")
        pan_core.initialize_pan()

        greeting = get_time_based_greeting()
        pan_speech.speak(
            f"{greeting} I'm Pan, ready to help you. How can I assist you today?"
        )

        # Start background thread for autonomous curiosity
        curiosity_thread = threading.Thread(target=curiosity_loop, daemon=True)
        curiosity_thread.start()

        user_id = "default_user"  # Replace with real user ID if available

        # Main conversation loop
        while True:
            try:
                user_input = listen_with_retries()
                if user_input:
                    print(f"User: {user_input}")
                    last_interaction_time = time.time()

                    user_input_lower = user_input.lower()

                    # Command processing
                    if "exit program" in user_input_lower:
                        pan_speech.speak("Goodbye! Shutting down now.")
                        print("Exiting program on user request.")
                        curiosity_active = False
                        curiosity_thread.join(timeout=5)
                        break

                    if user_input_lower.startswith("search for"):
                        search_query = user_input[10:].strip()
                        response = pan_research.live_search(search_query, user_id)
                    elif user_input_lower.startswith("weather"):
                        response = pan_research.get_weather()
                    elif user_input_lower.startswith("news"):
                        response = pan_research.get_local_news()

                    elif user_input_lower.startswith("share your thoughts"):
                        response = pan_research.list_opinions(user_id, share=True)
                    elif user_input_lower.startswith("adjust your opinion on"):
                        parts = user_input.split(" to ")
                        if len(parts) == 2:
                            topic = (
                                parts[0].replace("adjust your opinion on", "").strip()
                            )
                            new_thought = parts[1].strip()
                            pan_research.adjust_opinion(topic, new_thought)
                            response = f"Got it. I've adjusted my thoughts on {topic}."
                        else:
                            response = "Please use the format: Adjust your opinion on [topic] to [new thought]."
                    elif "joke" in user_input_lower:
                        jokes = [
                            "Why don't scientists trust atoms? Because they make up everything!",
                            "Why did the scarecrow win an award? Because he was outstanding in his field!",
                            "Why did the bicycle fall over? Because it was two-tired!",
                            "Why do programmers prefer dark mode? Because light attracts bugs!",
                        ]
                        response = random.choice(jokes)

                    else:
                        # General conversation handling
                        response = pan_conversation.respond(user_input, user_id)

                    # Adjust response based on user affinity level
                    user_affinity = pan_research.get_affinity(user_id)
                    if user_affinity < 0:
                        response = response.replace(
                            "I think", "Whatever, I guess"
                        ).replace("I hope", "I don't care if")

                    print(f"Pan: {response}")
                    pan_speech.speak(response)

                    time.sleep(0.3)  # pause to avoid Pan hearing itself
                else:
                    print("No valid input detected, listening again...")

            except KeyboardInterrupt:
                # Handle CTRL+C during conversation loop by immediately exiting
                print("\nInterrupted during conversation. Shutting down...")
                raise

    except KeyboardInterrupt:
        # Handle CTRL+C for graceful shutdown
        print("\nShutting down gracefully...")
        curiosity_active = False
        if "curiosity_thread" in locals():
            curiosity_thread.join(timeout=5)
        print("Pan has been shut down. Goodbye!")
        sys.exit(0)
