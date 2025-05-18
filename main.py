"""
PAN - Personal Assistant with Nuance

Main entry point for the PAN digital assistant. Handles initialization,
user interaction, command processing, and manages the autonomous curiosity system.
"""

import random
import signal
import sys
import threading
import time
from datetime import datetime

import pan_config  # Centralized Configuration
import pan_conversation
import pan_core
import pan_research
import pan_speech

# Global variables for tracking state
curiosity_active = True
last_interaction_time = time.time()
last_speech_time = 0


# Load Configuration Settings
def load_config():
    config = pan_config.get_config()
    global MAX_SHORT_TERM_MEMORY, IDLE_THRESHOLD_SECONDS, MIN_SPEECH_INTERVAL_SECONDS
    MAX_SHORT_TERM_MEMORY = config["conversation"]["max_short_term_memory"]
    IDLE_THRESHOLD_SECONDS = config["conversation"]["idle_threshold_seconds"]
    MIN_SPEECH_INTERVAL_SECONDS = config["conversation"]["min_speech_interval_seconds"]


load_config()


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
    global last_interaction_time, last_speech_time

    while curiosity_active:
        time.sleep(10)
        idle_time = time.time() - last_interaction_time

        if idle_time >= IDLE_THRESHOLD_SECONDS:
            topic = random.choice(["space", "history", "technology", "science"])
            assistant_name = pan_config.ASSISTANT_NAME
            print(f"{assistant_name} is curious about {topic}...")
            pan_speech.speak(
                f"I'm curious about {topic}. Let me see what I can find.",
                mood_override="curious",
            )

            response = pan_research.live_search(topic)
            print(f"{assistant_name}'s curiosity: {response}")
            pan_speech.speak(
                f"I just learned something amazing about {topic}! {response}"
            )

            last_speech_time = time.time()
            last_interaction_time = time.time()


def listen_with_retries(max_attempts=3, timeout=None):
    """
    Attempt to listen for user speech input with multiple retries on failure.

    This function ensures that PAN waits for any text-to-speech to finish before
    attempting to listen, and retries listening if no clear speech is detected.
    It also handles keyboard interrupts gracefully to allow clean exit.

    Args:
        max_attempts (int): Maximum number of listening attempts before giving up
        timeout (int, optional): Maximum time in seconds to wait for speech input on each attempt
                                If None, uses the configured default.

    Returns:
        str or None: Transcribed speech text if successful, None if all attempts fail

    Raises:
        KeyboardInterrupt: Re-raises keyboard interrupt to allow clean exit
    """
    global exit_requested

    for attempt in range(max_attempts):
        # Check if exit has been requested by signal handler
        if exit_requested:
            return None

        wait_start = time.time()
        wait_timeout = 10  # seconds - reduced to ensure faster response to CTRL+C
        last_log_time = 0

        # Wait for TTS to finish speaking before listening, with periodic interrupt checks
        try:
            while pan_speech.speak_manager.speaking_event.is_set():
                # Check if exit has been requested by signal handler
                if exit_requested:
                    return None

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
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected while waiting for TTS...")
            cleanup_and_exit()
            return None

        try:
            # Use recalibration on first attempt for better accuracy
            use_recalibration = attempt == 0
            text = pan_speech.listen_to_user(
                timeout=timeout, recalibrate=use_recalibration
            )

            # Check if exit has been requested by signal handler
            if exit_requested:
                return None

            if text:
                return text

            print(f"Listen attempt {attempt + 1} failed, retrying...")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected during speech recognition")
            cleanup_and_exit()
            return None

    print("Max listen attempts reached without success.")
    return None


# Global flag to track application state
exit_requested = False


def cleanup_and_exit():
    """Perform clean shutdown operations and exit."""
    global curiosity_active, exit_requested

    print("\nShutting down cleanly...")

    # Set global shutdown flag
    exit_requested = True

    # Stop the curiosity thread
    curiosity_active = False

    # Clean up speech-related resources using the manager's proper stop method
    try:
        # Use the SpeakManager's cleanup method which handles everything properly
        pan_speech.speak_manager.stop()

        # Small delay to allow thread cleanup
        time.sleep(0.2)
    except Exception as e:
        print(f"Error during speech engine cleanup: {e}")

    print("Goodbye!")
    sys.exit(0)


def signal_handler(_sig, _frame):
    """Handle keyboard interrupts gracefully."""
    print("\nKeyboard interrupt detected, exiting cleanly...")
    cleanup_and_exit()


if __name__ == "__main__":
    # Register the signal handler for CTRL+C
    signal.signal(signal.SIGINT, signal_handler)

    assistant_name = pan_config.ASSISTANT_NAME
    print(f"{assistant_name} is starting...")
    pan_core.initialize_pan()

    # Streamlined greeting with time-based introduction
    hour = datetime.now().hour
    time_greeting = (
        "Good morning"
        if 5 <= hour < 12
        else (
            "Good afternoon"
            if 12 <= hour < 17
            else "Good evening" if 17 <= hour < 22 else "Hello"
        )
    )

    # Full name explanation based on assistant name
    name_explanation = (
        "your Personal Assistant with Nuance" if assistant_name == "Pan" else ""
    )
    name_connector = ", " if name_explanation else ""

    try:
        pan_speech.speak(
            f"{time_greeting}! I'm {assistant_name}{name_connector}{name_explanation}. I can help you search for information, check the weather, get news updates, or just chat. What can I do for you today?"
        )

        curiosity_thread = threading.Thread(target=curiosity_loop, daemon=True)
        curiosity_thread.start()

        user_id = "default_user"

        while not exit_requested:
            try:
                user_input = listen_with_retries()
                if exit_requested:
                    break

                if user_input:
                    user_input_lower = user_input.lower()

                    if "exit program" in user_input_lower:
                        pan_speech.speak("Goodbye! Shutting down now.")
                        cleanup_and_exit()
                        break

                    # Process non-exit commands
                    response = pan_conversation.respond(user_input, user_id)
                    assistant_name = pan_config.ASSISTANT_NAME
                    print(f"{assistant_name}: {response}")
                    pan_speech.speak(response)
                else:
                    print("No valid input detected, listening again...")
            except KeyboardInterrupt:
                # This should be caught by the signal handler, but just in case
                cleanup_and_exit()
                break
    except Exception as e:
        print(f"Unexpected error: {e}")
        cleanup_and_exit()
    except KeyboardInterrupt:
        # This should be caught by the signal handler, but just in case
        cleanup_and_exit()
