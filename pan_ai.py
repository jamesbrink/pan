# pan_ai.py - Language Model Interface (GPT-Style)
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PanAI:
    def __init__(self):
        self.model_name = "gpt2"  # You can change this to any compatible model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def generate_response(self, prompt, max_length=100):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs, 
            max_length=max_length, 
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

pan_ai = PanAI()
