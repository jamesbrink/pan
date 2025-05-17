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

        Loads the pre-trained model and tokenizer, and sets up the appropriate
        device (GPU if available, otherwise CPU) for inference.
        """
        self.model_name = "gpt2"  # You can change this to any compatible model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()  # Set the model to evaluation mode

    def generate_response(self, prompt, max_length=100):
        """
        Generate a text response based on the given prompt.

        Uses the loaded language model to generate a continuation of the
        provided prompt text. Various parameters control the generation process
        to ensure quality and relevance.

        Args:
            prompt (str): The input text to generate a response from
            max_length (int, optional): Maximum length of the generated response
                                        in tokens. Defaults to 100.

        Returns:
            str: The generated text response
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,  # Prevent repetition of n-grams
            temperature=0.7,  # Control randomness (lower is more deterministic)
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response


# Global PanAI instance for use throughout the application
pan_ai = PanAI()
