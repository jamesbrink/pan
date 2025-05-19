import threading

from pan_ai import pan_ai  # Ensure pan_ai is properly imported
from pan_research import fetch_news, fetch_weather
from pan_speech import speak, stop_speaking


# Conversation state management class
class ConversationState:
    """Class to manage conversation state and context"""

    # Context Memory (Session-based)
    conversation_history: list[str] = []  # Only stores PAN's responses, not user input
    MAX_MEMORY_LENGTH = 10  # Number of exchanges before auto-summarization
    stop_generation_event = threading.Event()  # Event to interrupt response generation

    @classmethod
    def add_to_history(cls, message):
        """Add a message to conversation history"""
        cls.conversation_history.append(message)
        # Maintain memory length
        if len(cls.conversation_history) > cls.MAX_MEMORY_LENGTH:
            cls.conversation_history = cls.conversation_history[
                -cls.MAX_MEMORY_LENGTH :
            ]

    @classmethod
    def get_history(cls):
        """Get the full conversation history"""
        return cls.conversation_history

    @classmethod
    def clear_history(cls):
        """Clear the conversation history"""
        cls.conversation_history = []


def respond(user_input, user_id=None):  # pylint: disable=unused-argument
    """
    Generate a response to user input.

    Args:
        user_input (str): The user's input text
        user_id (str, optional): User identifier for personalization (not used currently)

    Returns:
        str: The assistant's response
    """
    if not user_input or user_input.strip() == "":
        return "Sorry, I didn't catch that."

    user_input_lower = user_input.lower()

    # Command: Stop Response Generation or Speaking
    if user_input_lower in ["stop", "cancel", "halt"]:
        ConversationState.stop_generation_event.set()  # Trigger the stop event
        stop_speaking()  # Immediately stop speaking
        print("[PAN] Response generation and speech stopped.")
        return "Okay, I've stopped."

    # Detect Commands (Weather, News)
    if "weather" in user_input_lower:
        return handle_weather()
    if "news" in user_input_lower:
        return handle_news()

    # Clear the stop event to allow fresh response generation
    ConversationState.stop_generation_event.clear()

    return gpt_neo_conversation(user_input)


def handle_weather():
    """Fetch and speak the weather."""
    try:
        weather_info = fetch_weather()
        response = f"The current weather is: {weather_info}"
        speak(response)
        return response
    except ValueError as e:
        print(f"[PAN ERROR] Weather API error: {e}")
        return "Sorry, there was an issue with the weather data format."
    except ConnectionError as e:
        print(f"[PAN ERROR] Weather connection failed: {e}")
        return "Sorry, I couldn't connect to the weather service."
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[PAN ERROR] Weather failed with unexpected error: {e}")
        return "Sorry, I encountered an unexpected issue while getting the weather information."


def handle_news():
    """Fetch and speak the news."""
    try:
        news_info = fetch_news()
        response = f"Here are the latest news headlines: {news_info}"
        speak(response)
        return response
    except ValueError as e:
        print(f"[PAN ERROR] News API error: {e}")
        return "Sorry, there was an issue with the news data format."
    except ConnectionError as e:
        print(f"[PAN ERROR] News connection failed: {e}")
        return "Sorry, I couldn't connect to the news service."
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[PAN ERROR] News failed with unexpected error: {e}")
        return "Sorry, I encountered an unexpected issue while getting the latest news."


def gpt_neo_conversation(prompt):
    """Generate a conversational response using the AI model"""

    # Only use PAN's responses for context
    context_text = "\n".join(ConversationState.get_history())
    print("Generating response... (Say 'stop' to interrupt)")

    # Start response generation in a separate thread
    response_thread = threading.Thread(
        target=generate_response_thread, args=(context_text, prompt)
    )
    response_thread.start()
    response_thread.join(
        timeout=10
    )  # Allow response to generate, but make it interruptible

    if ConversationState.stop_generation_event.is_set():
        print("[PAN] Response generation was interrupted.")
        return "Okay, I've stopped."

    # Retrieve the last response if not interrupted
    history = ConversationState.get_history()
    if history and history[-1].startswith("PAN: "):
        return history[-1].replace("PAN: ", "")

    return "Sorry, I couldn't generate a response."


def generate_response_thread(context_text, _):
    """
    Thread function for generating a response.

    Args:
        context_text (str): The conversation context
        _ (str): Unused parameter (previously prompt)
    """
    try:
        # Generate response using PAN's context only (no user text)
        response = pan_ai.generate_response(context_text + "\nPAN:", max_new_tokens=150)

        # If the stop event is triggered, abandon response
        if ConversationState.stop_generation_event.is_set():
            print("[PAN] Response generation interrupted.")
            return

        # Store only PAN's response in memory
        ConversationState.add_to_history(f"PAN: {response}")

        # Memory length is maintained by ConversationState.add_to_history

        speak(response)  # Immediately speak the response (interruptible)
    except ValueError as e:
        print(f"[PAN ERROR] Invalid input for response generation: {e}")
        ConversationState.add_to_history(
            "PAN: Sorry, I couldn't understand how to respond."
        )
    except RuntimeError as e:
        print(f"[PAN ERROR] Runtime error during response generation: {e}")
        ConversationState.add_to_history(
            "PAN: Sorry, I encountered an issue while thinking."
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[PAN ERROR] Unexpected error during response generation: {e}")
        ConversationState.add_to_history(
            "PAN: Sorry, I couldn't generate a response due to an unexpected issue."
        )


def summarize_memory():
    """Auto-Summarize conversation memory to prevent overflow."""
    history = ConversationState.get_history()

    if len(history) > ConversationState.MAX_MEMORY_LENGTH:
        summary = "\n".join(history[-ConversationState.MAX_MEMORY_LENGTH :])
        ConversationState.clear_history()
        ConversationState.add_to_history(summary)
        print("[PAN] Memory summarized.")
