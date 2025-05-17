"""
PAN Conversation Module

Handles user input, dynamically determines the response, and integrates
with the research and memory modules. Supports dynamic web search,
weather information, and conversation flow management.
"""

import pan_research
import pan_emotions
import pan_settings
import pan_speech
import random

# Respond to user input
def respond(user_input, user_id):
    if not user_input or user_input.strip() == "":
        return "Sorry, I didn't catch that."

    user_input_lower = user_input.lower()

    # Greeting detection
    if any(greet in user_input_lower for greet in ["hello", "hi", "hey", "greetings"]):
        return "Hello! How can I assist you today?"

    # Asking about Pan's mood or feelings
    if "how are you" in user_input_lower or "how do you feel" in user_input_lower:
        mood_response = pan_emotions.pan_emotions.express_feelings()
        return mood_response

    # Dynamic Weather Location Setting
    if user_input_lower.startswith("set default city to"):
        location = user_input_lower.replace("set default city to", "").strip()
        if "," in location:
            city, country = map(str.strip, location.split(","))
            pan_settings.pan_settings.set_default_location(city, country)
            return f"Default location set to {city}, {country}."
        else:
            pan_settings.pan_settings.set_default_location(location)
            return f"Default city set to {location}."

    # Weather queries (configurable)
    if "weather" in user_input_lower:
        city = pan_settings.pan_settings.DEFAULT_CITY
        country = pan_settings.pan_settings.DEFAULT_COUNTRY_CODE
        return pan_research.get_weather(city, country)

    # Local news queries
    if "news" in user_input_lower:
        return pan_research.get_local_news()

    # Direct search queries
    if any(prefix in user_input_lower for prefix in ["search for", "what is", "who is", "tell me about", "explain"]):
        query = user_input_lower.replace("search for", "").replace("what is", "").replace("who is", "").replace("tell me about", "").replace("explain", "").strip()
        return pan_research.live_search(query)

    # Multi-step research queries
    if "deep dive on" in user_input_lower:
        topic = user_input_lower.replace("deep dive on", "").strip()
        return pan_research.multi_step_research(topic)

    # User opinions
    if "your opinions" in user_input_lower or "what do you think" in user_input_lower:
        return pan_research.list_opinions(user_id, share=True)

    # Adjusting opinions
    if user_input_lower.startswith("adjust your opinion on"):
        parts = user_input.split(" to ")
        if len(parts) == 2:
            topic = parts[0].replace("adjust your opinion on", "").strip()
            new_thought = parts[1].strip()
            pan_settings.pan_settings.set_default_location(topic, new_thought)
            return f"I've adjusted my thoughts on {topic}."

    # Comfort user if sad
    if any(phrase in user_input_lower for phrase in ["i'm sad", "i feel down", "i feel lonely", "i'm depressed"]):
        return "I'm here for you. You're not alone."

    # Joke response
    if "joke" in user_input_lower:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why did the bicycle fall over? Because it was two-tired!",
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why don't programmers like nature? It has too many bugs!"
        ]
        return random.choice(jokes)

    # Custom memory-based responses
    if "remember" in user_input_lower:
        memory_content = user_input_lower.replace("remember", "").strip()
        pan_memory.store_memory(user_id, memory_content)
        return f"I'll remember that you said: {memory_content}"

    if "what do you remember" in user_input_lower:
        memories = pan_memory.retrieve_memories(user_id)
        if memories:
            return "Here's what I remember: " + ", ".join(memories)
        else:
            return "I don't seem to remember anything specific right now."

    # Curiosity-driven learning
    if "curious about" in user_input_lower:
        topic = user_input_lower.replace("curious about", "").strip()
        response = pan_research.live_search(topic)
        return f"I just learned something amazing about {topic}! {response}"

    # Affinity warning (for low affinity users)
    if "do you trust me" in user_input_lower:
        affinity = pan_research.get_affinity(user_id)
        if affinity < -5:
            return "I don't trust you much."
        return "Of course! We get along well."

    # Fallback to search if nothing else matches
    return pan_research.live_search(user_input)
