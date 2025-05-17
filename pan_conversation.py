"""
PAN Conversation Module (Enhanced with Local GPT-J, Context Memory, Memory Status, and Auto-Summarization)

Handles user input, dynamically determines the response, and integrates
with the research and memory modules. Supports dynamic web search,
weather information, and advanced conversational capabilities using GPT-J.
"""

import pan_research
import pan_emotions
import pan_settings
import pan_speech
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Initialize Local GPT-J Model
print("Loading GPT-J model...")
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B")
model.eval()
print("GPT-J model loaded successfully.")

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

    # Toggle GPT-J with Voice Command
    if "enable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(True)
        return "Advanced conversation enabled with GPT-J."

    if "disable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(False)
        return "Advanced conversation disabled. Switching to basic mode."

    # Check if GPT-J is enabled
    if hasattr(pan_settings.pan_settings, "USE_GPT2_FOR_CONVERSATION"):
        if pan_settings.pan_settings.USE_GPT2_FOR_CONVERSATION:
            return local_gptj_conversation(user_input)
        else:
            return rule_based_response(user_input)

    # Fallback to rule-based response
    return rule_based_response(user_input)


# Local GPT-J Conversation Function
def local_gptj_conversation(prompt):
    global conversation_history

    # Add user input to memory
    conversation_history.append(f"User: {prompt}")

    # Auto-Summarize if memory is too long
    if len(conversation_history) > MAX_MEMORY_LENGTH:
        summarize_memory()

    # Generate response with context memory
    context_text = "\n".join(conversation_history)
    print("DEBUG: Using GPT-J with context memory...")

    try:
        with torch.no_grad():
            inputs = tokenizer(context_text + "\nPAN:", return_tensors="pt")
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                pad_token_id=tokenizer.eos_token_id,
                max_length=150, 
                num_return_sequences=1, 
                do_sample=True, 
                temperature=0.7,
                top_p=0.9
            )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True).split("PAN:")[-1].strip()
    except Exception as e:
        response = f"Error with GPT-J: {str(e)}"

    # Store response in memory
    conversation_history.append(f"PAN: {response}")
    return response

# Auto-Summarize Memory
def summarize_memory():
    global conversation_history
    print("DEBUG: Summarizing conversation history...")
    summary_prompt = "\n".join(conversation_history) + "\nSummarize this conversation in one paragraph:"
    try:
        with torch.no_grad():
            inputs = tokenizer(summary_prompt, return_tensors="pt")
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                pad_token_id=tokenizer.eos_token_id,
                max_length=150,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            conversation_history = [f"CONVERSATION SUMMARY: {summary.strip()}"]
            print(f"DEBUG: Memory summarized: {summary.strip()}")
    except Exception as e:
        print(f"Error summarizing memory: {str(e)}")

# Clear Memory
def clear_memory():
    global conversation_history
    conversation_history.clear()

# Show Memory
def show_memory():
    if not conversation_history:
        return "I don't remember anything right now."

    return "Here's what I remember:\n" + "\n".join(conversation_history)

# Rule-Based Fallback Response
def rule_based_response(user_input):
    user_input = user_input.lower()
    
    if "how are you" in user_input:
        return "I'm just a program, but I'm here to help you."

    if "joke" in user_input:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why did the bicycle fall over? Because it was two-tired!",
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why don't programmers like nature? It has too many bugs!"
        ]
        return random.choice(jokes)

    if "i'm sad" in user_input or "i feel down" in user_input:
        return "I'm here for you. You're not alone."

    return "I'm not sure how to respond to that. Can you clarify?"
