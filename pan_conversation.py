"""
PAN Conversation Module (Enhanced with Local GPT-2)

Handles user input, dynamically determines the response, and integrates
with the research and memory modules. Supports dynamic web search,
weather information, and advanced conversational capabilities using GPT-2.
"""

import importlib
import pan_settings
import pan_research
import pan_emotions
import pan_speech
import random
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

# Reload settings to ensure latest configuration
importlib.reload(pan_settings)

# Initialize Local GPT-2 Model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
model.eval()

# Debug Print (Ensures GPT-2 Flag is Loaded)
print("DEBUG: GPT-2 Enabled:", hasattr(pan_settings.pan_settings, "USE_GPT2_FOR_CONVERSATION"))

# Respond to user input
def respond(user_input, user_id):
    if not user_input or user_input.strip() == "":
        return "Sorry, I didn't catch that."

    user_input_lower = user_input.lower()

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

    # Toggle GPT-2 with Voice Command
    if "enable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(True)
        return "Advanced conversation enabled."

    if "disable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(False)
        return "Advanced conversation disabled."

    # Check if GPT-2 is enabled
    if hasattr(pan_settings.pan_settings, "USE_GPT2_FOR_CONVERSATION"):
        if pan_settings.pan_settings.USE_GPT2_FOR_CONVERSATION:
            return local_gpt2_conversation(user_input)
        else:
            return rule_based_response(user_input)

    # Fallback to rule-based response
    return rule_based_response(user_input)


# Local GPT-2 Conversation Function (Improved)
def local_gpt2_conversation(prompt):
    try:
        with torch.no_grad():
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                pad_token_id=tokenizer.eos_token_id,
                max_length=100, 
                num_return_sequences=1, 
                do_sample=True, 
                temperature=0.7
            )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.strip()
    except Exception as e:
        return f"Error with GPT-2: {str(e)}"

# Rule-Based Fallback Response
def rule_based_response(user_input):
    if "how are you" in user_input.lower():
        return "I'm just a program, but I'm here to help you."

    if "joke" in user_input.lower():
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why did the bicycle fall over? Because it was two-tired!",
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why don't programmers like nature? It has too many bugs!"
        ]
        return random.choice(jokes)

    if "i'm sad" in user_input.lower() or "i feel down" in user_input.lower():
        return "I'm here for you. You're not alone."

    return "I'm not sure how to respond to that. Can you clarify?"
