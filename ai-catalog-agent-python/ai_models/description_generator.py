import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Optional
import logging
from pathlib import Path
import os

class DescriptionGenerator:
    """
    A class to generate product descriptions using fine-tuned language models.
    Supports both local model caching and cloud-based inference.
    """
    
    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_cache_dir = Path(os.getenv("MODEL_CACHE_DIR", "./model_cache"))
        self._prepare_model_cache()
        
    def _prepare_model_cache(self):
        """Create model cache directory if it doesn't exist"""
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_model(self):
        """
        Load the model and tokenizer either from cache or download from HuggingFace.
        Uses quantization for smaller memory footprint when possible.
        """
        try:
            # Try to load quantized version first
            quantized_model_path = self.model_cache_dir / f"{self.model_name}-quantized"
            if quantized_model_path.exists():
                logging.info(f"Loading quantized model from {quantized_model_path}")
                self.model = AutoModelForCausalLM.from_pretrained(
                    quantized_model_path,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
            else:
                logging.info(f"Loading model {self.model_name} from HuggingFace")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=self.model_cache_dir,
                    device_map="auto"
                )
                
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.model_cache_dir
            )
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Initialize pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device
            )
            
        except Exception as e:
            logging.error(f"Failed to load model: {str(e)}")
            raise RuntimeError("Model loading failed")

    def generate(self, product_data: Dict, language: str = "en") -> str:
        """
        Generate a product description based on input features.
        
        Args:
            product_data: Dictionary containing product attributes
            language: Target language for the description
            
        Returns:
            Generated description string
        """
        if self.generator is None:
            self.load_model()
        
        try:
            prompt = self._build_prompt(product_data, language)
            logging.info(f"Generating description with prompt: {prompt[:100]}...")
            
            # Generate with temperature sampling for diversity
            outputs = self.generator(
                prompt,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]['generated_text']
            description = self._post_process(generated_text, prompt)
            
            logging.info(f"Generated description: {description[:100]}...")
            return description
            
        except Exception as e:
            logging.error(f"Generation failed: {str(e)}")
            raise RuntimeError("Description generation failed")

    def _build_prompt(self, product_data: Dict, language: str) -> str:
        """Construct the prompt for the language model"""
        name = product_data.get("name", "product")
        category = product_data.get("category", "item")
        color = product_data.get("color", "")
        material = product_data.get("material", "")
        
        prompt = (
            f"Generate a professional e-commerce product description for {name} "
            f"in the {category} category. "
        )
        
        if color:
            prompt += f"Color: {color}. "
        if material:
            prompt += f"Material: {material}. "
            
        prompt += (
            f"The description should be in {language} and highlight key features "
            f"that would appeal to online shoppers. Include relevant details about "
            f"quality, usage, and benefits. Description:"
        )
        
        return prompt

    def _post_process(self, generated_text: str, prompt: str) -> str:
        """Clean up the generated text"""
        # Remove prompt from output
        description = generated_text[len(prompt):].strip()
        
        # Ensure proper sentence endings
        if description and description[-1] not in {".", "!", "?"}:
            last_punct = max(
                description.rfind("."),
                description.rfind("!"),
                description.rfind("?")
            )
            if last_punct > 0:
                description = description[:last_punct + 1]
        
        # Remove any incomplete sentences at start
        first_punct = min(
            description.find("."),
            description.find("!"),
            description.find("?")
        )
        if first_punct > 0:
            description = description[first_punct + 1:].strip()
        
        return description

# Singleton instance for the application
description_generator = DescriptionGenerator()

def generate_description(product_data: Dict, language: str = "en") -> str:
    """Public interface for description generation"""
    return description_generator.generate(product_data, language)