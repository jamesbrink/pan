"""
PAN - Personal Assistant with Nuance

Main entry point for the PAN digital assistant. Handles initialization, 
user interaction, command processing, and manages the autonomous curiosity system.
"""

import pan_core
import pan_conversation
import pan_emotions
import pan_memory
import pan_settings
import pan_speech
import pan_ai
import pan_research
import threading
import time
import random
from datetime import datetime

# Global variables for tracking state
curiosity_active = True
last_interaction_time = time.time()
last_speech_time = 0
MIN_SPEECH_INTERVAL = 15  # seconds

def get_time_based_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning!"
    elif 12 <= hour < 17:
        return "Good afternoon!"
    elif 17 <= hour < 22:
        return "Good evening!"
    else:
        return "Hello!"

def curiosity_loop():
    global last_interaction_time, last_speech_time
    idle_threshold = 5 * 60  # 5 minutes idle before curiosity triggers

    while curiosity_active:
        time.sleep(10)
        idle_time = time.time() - last_interaction_time
        if idle_time >= idle_threshold:
            topic = random.choice(["space", "history", "technology", "science"])
            response = pan_research.live_search(topic)
            pan_speech.speak(f"I just learned something amazing about {topic}! {response}")

            last_speech_time = time.time()
            last_interaction_time = time.time()

def listen_with_retries(max_attempts=3, timeout=5):
    for attempt in range(max_attempts):
        text = pan_speech.listen_to_user(timeout=timeout)
        if text:
            return text
        else:
            print(f"Listen attempt {attempt + 1} failed, retrying...")
            time.sleep(1)
    return None

if __name__ == '__main__':
    print("Pan is starting...")
    pan_core.initialize_pan()
    greeting = get_time_based_greeting()
    pan_speech.speak(f"{greeting} I'm Pan, ready to help you. How can I assist you today?")

    curiosity_thread = threading.Thread(target=curiosity_loop, daemon=True)
    curiosity_thread.start()

    user_id = "default_user"

    while True:
        user_input = listen_with_retries()
        if user_input:
            user_input_lower = user_input.lower()
            if "exit program" in user_input_lower:
                pan_speech.speak("Goodbye! Shutting down now.")
                curiosity_active = False
                curiosity_thread.join(timeout=5)
                break
            elif user_input_lower.startswith("search for"):
                search_query = user_input[10:].strip()
                response = pan_research.live_search(search_query)
            elif user_input_lower.startswith("weather"):
                response = pan_research.get_weather()
            elif user_input_lower.startswith("news"):
                response = pan_research.get_local_news()
            else:
                response = pan_conversation.respond(user_input, user_id)
            
            print(f"Pan: {response}")
            pan_speech.speak(response)
        else:
            print("No valid input detected, listening again...")
