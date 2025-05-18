"""
PAN Conversation Module (Enhanced with Local LLM, Context Memory, Memory Status, and Auto-Summarization)

Handles user input, dynamically determines the response, and integrates
with the research and memory modules. Supports dynamic web search,
weather information, and advanced conversational capabilities using configurable LLM models.
"""

import random

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import pan_config
import pan_research
import pan_settings

# Initialize Conversation Model from settings
print(f"Loading conversation model: {pan_config.CONVERSATION_MODEL_NAME}...")

# Get context length and quantization level from config
context_length = pan_config.MODEL_CONTEXT_LENGTH
quantization_level = pan_config.MODEL_QUANTIZATION_LEVEL

print(f"Using context length: {context_length} tokens and quantization level: {quantization_level}")

# Configure tokenizer with appropriate context length
tokenizer = AutoTokenizer.from_pretrained(
    pan_config.CONVERSATION_MODEL_NAME,
    model_max_length=context_length
)

# Set up quantization configuration
quantization_config = None
try:
    if quantization_level.lower() in ("4bit", "8bit"):
        bits = 4 if quantization_level.lower() == "4bit" else 8
        # Check if bitsandbytes is available with required features
        try:
            import bitsandbytes
            bnb_version = getattr(bitsandbytes, "__version__", "0.0.0")
            if bits == 4 and tuple(map(int, bnb_version.split("."))) < (0, 41, 0):
                print(f"Warning: bitsandbytes version {bnb_version} may not support 4-bit quantization. Using 8-bit instead.")
                bits = 8
                
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=bits == 4,
                load_in_8bit=bits == 8,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            print(f"Using {bits}-bit quantization for model loading")
        except (ImportError, AttributeError):
            print("Warning: bitsandbytes not available or not supported, using 8-bit quantization instead")
            try:
                # Try simple 8-bit loading as fallback
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True
                )
                print("Using 8-bit quantization as fallback")
            except Exception as e:
                print(f"Warning: Quantization not supported, falling back to standard loading: {e}")
                quantization_level = "none"
except Exception as e:
    print(f"Warning: Error setting up quantization, falling back to standard loading: {e}")

# Load the model with appropriate config
model_kwargs = {}
if quantization_config:
    model_kwargs["quantization_config"] = quantization_config

model = AutoModelForCausalLM.from_pretrained(
    pan_config.CONVERSATION_MODEL_NAME,
    **model_kwargs
)

# Only move to device if not using quantization (quantized models handle this differently)
if quantization_level.lower() == "none":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

model.eval()
print(f"Conversation model loaded successfully: {pan_config.CONVERSATION_MODEL_NAME}")

# Context Memory (Session-based)
conversation_history = []


# Respond to user input
def respond(user_input, _user_id):  # Prefix unused parameter with underscore
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
    if any(
        prefix in user_input_lower for prefix in ["search for", "what is", "who is"]
    ):
        query = (
            user_input_lower.replace("search for", "")
            .replace("what is", "")
            .replace("who is", "")
            .strip()
        )
        return pan_research.live_search(query)

    # Weather command
    if "weather" in user_input_lower:
        city = pan_settings.pan_settings.DEFAULT_CITY
        country = pan_settings.pan_settings.DEFAULT_COUNTRY_CODE
        return pan_research.get_weather(city, country)

    # News command
    if "news" in user_input_lower:
        return pan_research.get_local_news()

    # Toggle advanced conversation with Voice Command
    if "enable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(True)
        return (
            f"Advanced conversation enabled with {pan_config.CONVERSATION_MODEL_NAME}."
        )

    if "disable advanced conversation" in user_input_lower:
        pan_settings.pan_settings.set_use_gpt2(False)
        return "Advanced conversation disabled. Switching to basic mode."

    # Check if advanced conversation is enabled
    if hasattr(pan_settings.pan_settings, "USE_GPT2_FOR_CONVERSATION"):
        if pan_settings.pan_settings.USE_GPT2_FOR_CONVERSATION:
            return local_llm_conversation(user_input)
        return rule_based_response(user_input)  # Removed unnecessary else

    # Fallback to rule-based response
    return rule_based_response(user_input)


# Local LLM Conversation Function
def local_llm_conversation(prompt):
    # Explicitly mark that we are modifying the global variable
    global conversation_history

    # Format user input based on model
    model_name = pan_config.CONVERSATION_MODEL_NAME.lower()
    
    if "qwen" in model_name:
        # For Qwen models, use their chat format
        user_message = f"<|im_start|>user\n{prompt}<|im_end|>"
    else:
        # Default format
        user_message = f"User: {prompt}"
        
    # Add user input to memory
    conversation_history.append(user_message)

    # Auto-Summarize if memory is too long
    if len(conversation_history) > pan_config.MAX_MEMORY_LENGTH:
        summarize_memory()

    # Generate response with context memory
    context_text = "\n".join(conversation_history)
    print(f"DEBUG: Using {pan_config.CONVERSATION_MODEL_NAME} with context memory...")
    
    # Determine the model-specific prompt format
    # Different models have different prompt formats
    model_name = pan_config.CONVERSATION_MODEL_NAME.lower()
    assistant_name = pan_config.ASSISTANT_NAME
    
    if "qwen" in model_name:
        # Qwen models use a specific chat format
        prompt_format = f"{context_text}\n<|im_start|>assistant"
        response_sep = "<|im_start|>assistant"
    else:
        # Default format for other models
        prompt_format = f"{context_text}\n{assistant_name}:"
        response_sep = f"{assistant_name}:"

    try:
        with torch.no_grad():
            inputs = tokenizer(prompt_format, return_tensors="pt")
            
            # Use a reasonable max_length relative to the configured context length
            # For generation we want to limit to a portion of the total context to avoid OOM errors
            max_gen_length = min(pan_config.MODEL_CONTEXT_LENGTH, int(pan_config.MODEL_CONTEXT_LENGTH * 0.25) + len(inputs.input_ids[0]))
            
            # Move inputs to the right device based on quantization settings
            if pan_config.MODEL_QUANTIZATION_LEVEL.lower() == "none":
                device = next(model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
            
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                pad_token_id=tokenizer.eos_token_id,
                max_length=max_gen_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Process the response based on the model format
            if "qwen" in model_name:
                # For Qwen models, the response comes after the assistant tag
                if "<|im_start|>assistant" in full_response:
                    response = full_response.split("<|im_start|>assistant")[-1].strip()
                else:
                    response = full_response.split(context_text)[-1].strip()
            else:
                # For other models, split on the assistant name
                response = full_response.split(f"{assistant_name}:")[-1].strip()
            
    except Exception as e:
        response = f"Error with language model: {str(e)}"

    # Store response in memory with proper formatting
    model_name = pan_config.CONVERSATION_MODEL_NAME.lower()
    assistant_name = pan_config.ASSISTANT_NAME
    
    if "qwen" in model_name:
        # For Qwen models, use their chat format
        assistant_message = f"<|im_start|>assistant\n{response}<|im_end|>"
    else:
        # Default format
        assistant_message = f"{assistant_name}: {response}"
        
    conversation_history.append(assistant_message)
    return response


# Auto-Summarize Memory
def summarize_memory():
    global conversation_history
    print("DEBUG: Summarizing conversation history...")
    
    # Get the base conversation text
    conversation_text = "\n".join(conversation_history)
    
    # Determine the model-specific prompt format
    model_name = pan_config.CONVERSATION_MODEL_NAME.lower()
    assistant_name = pan_config.ASSISTANT_NAME
    
    if "qwen" in model_name:
        # Qwen models use a specific chat format
        summary_prompt = f"{conversation_text}\n<|im_start|>user\nSummarize this conversation in one paragraph.<|im_end|>\n<|im_start|>assistant"
    else:
        # Default format for other models
        summary_prompt = f"{conversation_text}\nSummarize this conversation in one paragraph:"
    
    try:
        with torch.no_grad():
            inputs = tokenizer(summary_prompt, return_tensors="pt")
            
            # Use a reasonable max_length relative to the configured context length
            max_gen_length = min(pan_config.MODEL_CONTEXT_LENGTH, int(pan_config.MODEL_CONTEXT_LENGTH * 0.25) + len(inputs.input_ids[0]))
            
            # Move inputs to the right device based on quantization settings
            if pan_config.MODEL_QUANTIZATION_LEVEL.lower() == "none":
                device = next(model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                pad_token_id=tokenizer.eos_token_id,
                max_length=max_gen_length,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Process the summary based on the model format
            if "qwen" in model_name:
                # For Qwen models, the response comes after the assistant tag
                if "<|im_start|>assistant" in full_response:
                    summary = full_response.split("<|im_start|>assistant")[-1].strip()
                else:
                    summary = full_response.split(conversation_text)[-1].strip()
            else:
                # For other models, we look for the summary part
                if "Summarize this conversation" in full_response:
                    summary = full_response.split("Summarize this conversation in one paragraph:")[-1].strip()
                else:
                    summary = full_response.split(conversation_text)[-1].strip()
            
            conversation_history = [f"CONVERSATION SUMMARY: {summary.strip()}"]
            print(f"DEBUG: Memory summarized: {summary.strip()}")
    except Exception as e:
        print(f"Error summarizing memory: {str(e)}")


# Clear Memory
def clear_memory():
    # Explicitly mark that we are modifying the global variable
    global conversation_history
    # Clear the conversation history list
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
            "Why don't programmers like nature? It has too many bugs!",
        ]
        return random.choice(jokes)

    if "i'm sad" in user_input or "i feel down" in user_input:
        return "I'm here for you. You're not alone."

    return "I'm not sure how to respond to that. Can you clarify?"
