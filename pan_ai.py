"""
Language Model Interface for PAN

This module provides a wrapper around transformer-based language models,
allowing PAN to generate natural language responses. It uses the Hugging Face
transformers library to load and run inference with pre-trained language models.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class PanAI:
    """
    Interface to transformer-based language models for text generation.

    This class handles the loading, initialization, and inference of
    transformer-based language models to generate human-like text responses.
    """

    def __init__(self):
        """
        Initialize the language model and tokenizer.

        Dynamically selects GPU (CUDA) with BitsAndBytes if available,
        otherwise falls back to CPU (standard precision).
        """
        self.model_name = "EleutherAI/gpt-neo-1.3B"  # Smaller, faster model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
        )
        self.model.to(self.device)
        self.model.eval()  # Set the model to evaluation mode

    def generate_response(self, prompt, max_new_tokens=150):
        """
        Generate a text response based on the given prompt.

        Args:
            prompt (str): The input text to generate a response from
            max_new_tokens (int, optional): Maximum length of the generated response

        Returns:
            str: The generated text response
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_return_sequences=1,
            do_sample=True,  # Allow sampling (needed for temperature)
            temperature=0.7,  # Control randomness (lower is more deterministic)
            no_repeat_ngram_size=2,  # Prevent repetition of n-grams
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response


# Global PanAI instance for use throughout the application
pan_ai = PanAI()
