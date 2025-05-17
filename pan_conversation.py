# pan_conversation.py - Handles user conversations with persistent user recognition

import pan_research
import pan_emotions
import pan_users
from pan_speech import speak

def respond(user_input, user_id):
    # Check if user is known
    name = pan_users.get_user_name(user_id)

    if not name:
        speak("I don't believe we've met. What's your name?", mood_override="curious")
        # For demo, prompt for name input; replace with voice recognition in production
        name = input("Please enter your name: ").strip()
        pan_users.add_user(user_id, name)
        speak(f"Nice to meet you, {name}!", mood_override="happy")

    if user_input is None or user_input.strip() == "":
        response = "I didn't catch that. Could you please repeat?"
        speak(response, mood_override="sad")
        return response

    user_input_lower = user_input.lower()

    # Greeting detection
    if any(greet in user_input_lower for greet in ["hello", "hi", "hey", "greetings"]):
        response = f"Hello, {name}! How can I assist you today?"
        speak(response, mood_override="happy")
        return response

    # Asking about Pan's mood or feelings
    if "how are you" in user_input_lower or "how do you feel" in user_input_lower:
        mood_response = pan_emotions.pan_emotions.express_feelings()
        speak(mood_response)
        return mood_response

    # Asking Pan's opinions
    if "your opinions" in user_input_lower or "what do you think" in user_input_lower:
        opinions = pan_research.list_opinions(user_id, share=True)
        return opinions

    # Weather queries
    if "weather" in user_input_lower:
        response = pan_research.get_weather()
        speak(response, mood_override="excited")
        return response

    # Local news queries
    if "news" in user_input_lower:
        response = pan_research.get_local_news()
        speak(response, mood_override="excited")
        return response

    # News archive request
    if "news archive" in user_input_lower or "show me the news archive" in user_input_lower:
        response = pan_research.list_news_archive()
        speak(response, mood_override="calm")
        return response

    # Multi-step research queries
    if user_input_lower.startswith("tell me about") or user_input_lower.startswith("explain"):
        topic = user_input_lower.replace("tell me about", "").replace("explain", "").strip()
        response = pan_research.multi_step_research(topic, user_id)
        return response

    # Comfort user if sad or favorite
    if "i'm sad" in user_input_lower or "i feel down" in user_input_lower:
        pan_research.comfort_user(user_id)
        return "I'm here for you. You're not alone."

    # Warn user if low affinity
    warning = pan_research.warn_low_affinity(user_id)
    if warning:
        return warning

    # Fallback - delegate to research module
    response = pan_research.live_search(user_input, user_id)
    return response
