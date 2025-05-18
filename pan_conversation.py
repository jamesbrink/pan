import threading
from pan_speech import speak, stop_speaking
from pan_ai import pan_ai  # Ensure pan_ai is properly imported
from pan_research import fetch_news, fetch_weather

# Context Memory (Session-based)
conversation_history = []  # Only stores PAN's responses, not user input
MAX_MEMORY_LENGTH = 10  # Number of exchanges before auto-summarization
stop_generation_event = threading.Event()  # Event to interrupt response generation

def respond(user_input, user_id):
    if not user_input or user_input.strip() == "":
        return "Sorry, I didn't catch that."

    user_input_lower = user_input.lower()

    # Command: Stop Response Generation or Speaking
    if user_input_lower in ["stop", "cancel", "halt"]:
        stop_generation_event.set()  # Trigger the stop event
        stop_speaking()             # Immediately stop speaking
        print("[PAN] Response generation and speech stopped.")
        return "Okay, I've stopped."

    # Detect Commands (Weather, News)
    if "weather" in user_input_lower:
        return handle_weather()
    if "news" in user_input_lower:
        return handle_news()

    # Clear the stop event to allow fresh response generation
    stop_generation_event.clear()
    
    return gpt_neo_conversation(user_input)

def handle_weather():
    """Fetch and speak the weather."""
    try:
        weather_info = fetch_weather()
        response = f"The current weather is: {weather_info}"
        speak(response)
        return response
    except Exception as e:
        print(f"[PAN ERROR] Weather failed: {e}")
        return "Sorry, I couldn't get the weather information."

def handle_news():
    """Fetch and speak the news."""
    try:
        news_info = fetch_news()
        response = f"Here are the latest news headlines: {news_info}"
        speak(response)
        return response
    except Exception as e:
        print(f"[PAN ERROR] News failed: {e}")
        return "Sorry, I couldn't get the latest news."

def gpt_neo_conversation(prompt):
    global conversation_history, stop_generation_event

    # Only use PAN's responses for context
    context_text = "\n".join(conversation_history)
    print("Generating response... (Say 'stop' to interrupt)")

    # Start response generation in a separate thread
    response_thread = threading.Thread(target=generate_response_thread, args=(context_text, prompt))
    response_thread.start()
    response_thread.join(timeout=10)  # Allow response to generate, but make it interruptible

    if stop_generation_event.is_set():
        print("[PAN] Response generation was interrupted.")
        return "Okay, I've stopped."

    # Retrieve the last response if not interrupted
    if conversation_history and conversation_history[-1].startswith("PAN: "):
        return conversation_history[-1].replace("PAN: ", "")
    
    return "Sorry, I couldn't generate a response."

def generate_response_thread(context_text, prompt):
    global conversation_history, stop_generation_event

    try:
        # Generate response using PAN's context only (no user text)
        response = pan_ai.generate_response(context_text + "\nPAN:", max_new_tokens=150)
        
        # If the stop event is triggered, abandon response
        if stop_generation_event.is_set():
            print("[PAN] Response generation interrupted.")
            return

        # Store only PAN's response in memory
        conversation_history.append(f"PAN: {response}")

        # Maintain memory length
        if len(conversation_history) > MAX_MEMORY_LENGTH:
            conversation_history = conversation_history[-MAX_MEMORY_LENGTH:]

        speak(response)  # Immediately speak the response (interruptible)
    except Exception as e:
        print(f"[PAN ERROR] Failed to generate response: {e}")
        conversation_history.append("PAN: Sorry, I couldn't generate a response.")

def summarize_memory():
    """Auto-Summarize conversation memory to prevent overflow."""
    global conversation_history

    if len(conversation_history) > MAX_MEMORY_LENGTH:
        summary = "\n".join(conversation_history[-MAX_MEMORY_LENGTH:])
        conversation_history = [summary]
        print("[PAN] Memory summarized.")
