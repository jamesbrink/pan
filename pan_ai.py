"""
Language Model Interface for PAN

This module provides a wrapper around transformer-based language models,
allowing PAN to generate natural language responses. It uses the Hugging Face
transformers library to load and run inference with pre-trained language models.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import pan_config


class PanAI:
    """
    Interface to transformer-based language models for text generation.

    This class handles the loading, initialization, and inference of
    transformer-based language models to generate human-like text responses.
    """

    def __init__(self):
        """
        Initialize the language model and tokenizer.

        Loads the pre-trained model and tokenizer from environment settings,
        and sets up the appropriate device (GPU if available, otherwise CPU) for inference.
        Supports configuration of model context length and quantization level.
        """
        self.model_name = pan_config.LLM_MODEL_NAME
        self.context_length = pan_config.MODEL_CONTEXT_LENGTH
        self.quantization_level = pan_config.MODEL_QUANTIZATION_LEVEL
        
        print(f"Loading model {self.model_name} with context length {self.context_length} and quantization {self.quantization_level}")
        
        # Configure tokenizer with appropriate context length
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            model_max_length=self.context_length
        )
        
        # Set up quantization configuration
        quantization_config = None
        try:
            if self.quantization_level.lower() in ("4bit", "8bit"):
                bits = 4 if self.quantization_level.lower() == "4bit" else 8
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
                    print("Warning: bitsandbytes not available or not supported, falling back to standard loading")
                    self.quantization_level = "none"
        except Exception as e:
            print(f"Warning: Error setting up quantization, falling back to standard loading: {e}")
            self.quantization_level = "none"
        
        # Load the model with appropriate config
        model_kwargs = {}
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **model_kwargs
        )
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Only move to device if not using quantization (quantized models handle this differently)
        if self.quantization_level.lower() == "none":
            self.model.to(self.device)
            
        self.model.eval()  # Set the model to evaluation mode

    def generate_response(self, prompt, max_length=100):
        """
        Generate a text response based on the given prompt.

        Uses the loaded language model to generate a continuation of the
        provided prompt text. Various parameters control the generation process
        to ensure quality and relevance. Supports different model types and formats.

        Args:
            prompt (str): The input text to generate a response from
            max_length (int, optional): Maximum length of the generated response
                                        in tokens. Defaults to 100.

        Returns:
            str: The generated text response
        """
        # Format the prompt based on the model
        model_name = self.model_name.lower()
        
        # Different models may require specific prompt formatting
        if "qwen" in model_name:
            # For Qwen models, use their chat format
            formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
        else:
            # Default format for regular completion models
            formatted_prompt = prompt
        
        # Prepare the inputs and generate
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
        
        # Move to the right device if not using quantization
        if self.quantization_level.lower() == "none":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
        outputs = self.model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=max_length + len(inputs.input_ids[0]),  # Account for prompt length
            num_return_sequences=1,
            no_repeat_ngram_size=2,  # Prevent repetition of n-grams
            temperature=0.7,  # Control randomness (lower is more deterministic)
            pad_token_id=self.tokenizer.eos_token_id,
        )
        
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the actual response based on model format
        if "qwen" in model_name:
            # For Qwen models, extract text after the assistant tag
            if "<|im_start|>assistant" in full_response:
                response = full_response.split("<|im_start|>assistant")[-1].strip()
            else:
                response = full_response.strip()
        else:
            # For other models, just use the whole response
            response = full_response.replace(prompt, "").strip()
            
        return response


# Global PanAI instance for use throughout the application
pan_ai = PanAI()
