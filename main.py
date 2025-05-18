"""
PAN - Personal Assistant with Nuance

Main entry point for the PAN digital assistant. Handles initialization,
user interaction, command processing, and manages the autonomous curiosity system.
"""

import argparse
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
import platform

# Global variables for tracking state
curiosity_active = True
last_interaction_time = time.time()
last_speech_time = 0
keyword_activated = False


# Load Configuration Settings
def load_config():
    config = pan_config.get_config()
    global MAX_SHORT_TERM_MEMORY, IDLE_THRESHOLD_SECONDS, MIN_SPEECH_INTERVAL_SECONDS
    global USE_KEYWORD_ACTIVATION, CONTINUOUS_LISTENING
    
    MAX_SHORT_TERM_MEMORY = config["conversation"]["max_short_term_memory"]
    IDLE_THRESHOLD_SECONDS = config["conversation"]["idle_threshold_seconds"]
    MIN_SPEECH_INTERVAL_SECONDS = config["conversation"]["min_speech_interval_seconds"]
    
    # Load keyword activation settings
    USE_KEYWORD_ACTIVATION = config["speech_recognition"]["use_keyword_activation"]
    CONTINUOUS_LISTENING = config["speech_recognition"]["continuous_listening"]


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


def check_macos_microphone_permissions():
    """
    On macOS, check if microphone permissions might be an issue and provide guidance.
    """
    if platform.system() != "Darwin":
        return
        
    try:
        # Try to just list microphones as a simple permissions check
        import speech_recognition as sr
        mic_list = sr.Microphone.list_microphone_names()
        
        if not mic_list:
            print("\n" + "="*60)
            print(" "*10 + "*** MACOS MICROPHONE PERMISSION ALERT ***")
            print("="*60)
            print("No microphones were detected on your macOS system!")
            print("This usually means Terminal or your IDE needs microphone permission.")
            print("\nTo fix this:")
            print("1. Open System Preferences > Security & Privacy > Privacy > Microphone")
            print("2. Make sure Terminal or your IDE has permission to access the microphone")
            print("3. You might need to quit Terminal/IDE completely and restart it")
            print("4. Try launching from a different Terminal window if using Nix")
            print("\nThe application will continue, but speech recognition will not work")
            print("until you grant microphone permissions!")
            print("="*60 + "\n")
    except Exception as e:
        print(f"Error checking microphone permissions: {e}")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='PAN - Personal Assistant with Nuance')
    parser.add_argument('--test-mic', action='store_true',
                        help='Run microphone test and exit')
    args = parser.parse_args()
    
    # Special case: if running microphone test, just do that and exit
    if args.test_mic:
        pan_speech.test_microphone()
        sys.exit(0)
    
    # Register the signal handler for CTRL+C
    signal.signal(signal.SIGINT, signal_handler)

    # Check for microphone permissions on macOS
    check_macos_microphone_permissions()

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

    # Add continuous listening mode information if enabled
    wake_word_info = ""
    if USE_KEYWORD_ACTIVATION and CONTINUOUS_LISTENING:
        wake_word_info = f" I'm in continuous listening mode, so you can activate me anytime by saying '{assistant_name}'."
    
    try:
        pan_speech.speak(
            f"{time_greeting}! I'm {assistant_name}{name_connector}{name_explanation}.{wake_word_info} I can help you search for information, check the weather, get news updates, or just chat. What can I do for you today?"
        )

        curiosity_thread = threading.Thread(target=curiosity_loop, daemon=True)
        curiosity_thread.start()

        user_id = "default_user"

        while not exit_requested:
            try:
                # Use keyword detection if enabled
                if USE_KEYWORD_ACTIVATION and CONTINUOUS_LISTENING:
                    # Wait for the wake word (assistant name)
                    keyword_detected = False
                    while not keyword_detected and not exit_requested:
                        try:
                            keyword_detected = pan_speech.listen_for_keyword()
                            if keyword_detected:
                                # Wake word detected, break out of the loop
                                assistant_name = pan_config.ASSISTANT_NAME
                                print(f"Wake word '{assistant_name}' detected! Listening for command...")
                                # Give a brief acknowledgment to let the user know it's listening
                                # Wait a moment to make sure any previous TTS operations are completed
                                time.sleep(0.5)
                                try:
                                    pan_speech.speak("Yes?", mood_override="curious")
                                    # Give time for the speech to start before continuing
                                    time.sleep(0.5)
                                except Exception as e:
                                    print(f"Error acknowledging wake word: {e}")
                                break
                            
                            # Counter to detect if we're having wake word detection issues
                            # This will let us show a helpful message after several attempts
                            if not hasattr(listen_for_keyword, 'attempt_counter'):
                                listen_for_keyword.attempt_counter = 0
                            
                            listen_for_keyword.attempt_counter += 1
                            
                            # After several attempts, show a message about potential mic issues
                            if listen_for_keyword.attempt_counter % 20 == 0:
                                platform_name = platform.system()
                                if platform_name == "Darwin":  # macOS
                                    print("\nTip: Not detecting wake word? You may have microphone permission issues.")
                                    print("Run with '--test-mic' to diagnose, or check System Preferences > Privacy > Microphone\n")
                                else:
                                    print("\nTip: Not detecting wake word? Try running with '--test-mic' to diagnose microphone issues\n")
                                
                            # Brief pause to prevent CPU overuse
                            time.sleep(0.1)
                        except KeyboardInterrupt:
                            cleanup_and_exit()
                            break
                    
                    # If exit was requested during keyword detection, break out
                    if exit_requested:
                        break
                
                # Now listen for the actual command
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
                    
                    # Reset the last interaction time
                    last_interaction_time = time.time()
                else:
                    print("No valid input detected, listening again...")
                    
                    # In continuous listening mode, go back to listening for wake word
                    if USE_KEYWORD_ACTIVATION and CONTINUOUS_LISTENING:
                        print(f"Returning to wake word detection mode. Say '{pan_config.ASSISTANT_NAME}' to activate.")
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
