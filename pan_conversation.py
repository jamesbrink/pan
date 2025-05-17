"""
PAN Conversation Module with GPT-Neo (2.7B)

Handles user input, dynamically determines the response, and integrates
with the research and memory modules. Supports dynamic web search,
weather information, and advanced conversational capabilities.
"""

import pan_research
import pan_emotions
import pan_settings
import pan_speech
import random
from pan_ai import pan_ai

# Context Memory (Session-based)
conversation_history = []
MAX_MEMORY_LENGTH = 10  # Number of exchanges before auto-summarization

# Respond to user input
def respond(user_input, user_id):
    if not user_input or user_input.strip() == "":
        return "Sorry, I didn't catch that."

    user_input_lower = user_input.lower()

    # Command: Forget Conversation
    if "forget everything we discussed" in user_input_lower:
        clear_memory()
        return "I've forgotten everything we discussed."

    # Command: Show Memory
    if "what do you remember" in user_input_lower:
        return show_memory()

    # Direct search commands
    if any(prefix in user_input_lower for prefix in ["search for", "what is", "who is"]):
        query = user_input_lower.replace("search for", "").replace("what is", "").replace("who is", "").strip()
        return pan_research.live_search(query)

    # Weather command
    if "weather" in user_input_lower:
        city = pan_settings.pan_settings.DEFAULT_CITY
        country = pan_settings.pan_settings.DEFAULT_COUNTRY_CODE
        return pan_research.get_weather(city, country)

    # News command
    if "news" in user_input_lower:
        return pan_research.get_local_news()

    # Use GPT-Neo for advanced conversation
    return gpt_neo_conversation(user_input)


# GPT-Neo Conversation Function
def gpt_neo_conversation(prompt):
    global conversation_history

    # Add user input to memory
    conversation_history.append(f"User: {prompt}")

    # Auto-Summarize if memory is too long
    if len(conversation_history) > MAX_MEMORY_LENGTH:
        summarize_memory()

    # Generate response with context memory
    context_text = "\n".join(conversation_history)
    response = pan_ai.generate_response(context_text + "\nPAN:", max_length=150)

    # Store response in memory
    conversation_history.append(f"PAN: {response}")
    return response

# Auto-Summarize Memory
def summarize_memory():
    global conversation_history
    summary_prompt = "\n".join(conversation_history) + "\nSummarize this conversation in one paragraph:"
    summary = pan_ai.generate_response(summary_prompt, max_length=100)
    conversation_history = [f"CONVERSATION SUMMARY: {summary.strip()}"]

# Clear Memory
def clear_memory():
    global conversation_history
    conversation_history.clear()

# Show Memory
def show_memory():
    if not conversation_history:
        return "I don't remember anything right now."
    return "Here's what I remember:\n" + "\n".join(conversation_history)
