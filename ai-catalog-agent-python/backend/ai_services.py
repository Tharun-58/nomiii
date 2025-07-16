import logging
import requests
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import config

class AIService:
    """Handles AI-related operations for the catalog"""
    
    def __init__(self):
        self.description_generator = None
        self.translation_model = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize AI models with lazy loading"""
        try:
            # Initialize description generator
            self.description_generator = pipeline(
                'text-generation',
                model='gpt2',
                device=0 if torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            # Initialize translation model (small model for demo)
            self.translation_tokenizer = AutoTokenizer.from_pretrained(
                "Helsinki-NLP/opus-mt-en-hi"
            )
            self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(
                "Helsinki-NLP/opus-mt-en-hi"
            )
            
            if torch.cuda.is_available():
                self.translation_model = self.translation_model.cuda()
                
            logging.info("AI models initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize AI models: {str(e)}")
            raise

    def generate_description(self, product_data, language='en'):
        """
        Generate product description using AI
        
        Args:
            product_data (dict): Product information
            language (str): Target language
            
        Returns:
            str: Generated description
        """
        try:
            if not self.description_generator:
                self._initialize_models()
                
            # Prepare prompt
            name = product_data.get('name', 'product')
            category = product_data.get('category', 'item')
            color = product_data.get('color', '')
            material = product_data.get('material', '')
            
            prompt = f"Create a professional product description for {name} "
            prompt += f"({category}) "
            
            if color:
                prompt += f"in {color} color "
            if material:
                prompt += f"made of {material} "
                
            prompt += f"that will appeal to online shoppers. Description in {language}:"
            
            # Generate description
            result = self.description_generator(
                prompt,
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                do_sample=True
            )
            
            description = result[0]['generated_text'].replace(prompt, '').strip()
            
            # Clean up description
            if description and description[-1] not in ['.', '!', '?']:
                last_period = description.rfind('.')
                if last_period != -1:
                    description = description[:last_period + 1]
                    
            logging.info("Description generated successfully")
            return description
            
        except Exception as e:
            logging.error(f"Description generation failed: {str(e)}")
            raise RuntimeError("Failed to generate description")

    def translate_text(self, text, source_lang, target_lang):
        """
        Translate text between languages
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        try:
            # For demo purposes, we're using a small English-Hindi model
            # In production, you'd use a proper multilingual model
            
            if source_lang == 'en' and target_lang == 'hi':
                if not self.translation_model:
                    self._initialize_models()
                    
                inputs = self.translation_tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                )
                
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                outputs = self.translation_model.generate(**inputs)
                translated = self.translation_tokenizer.decode(
                    outputs[0],
                    skip_special_tokens=True
                )
                
                logging.info("Text translated successfully")
                return translated
                
            else:
                # Fallback to simple return for unsupported languages
                logging.warning(
                    f"Unsupported translation pair: {source_lang}->{target_lang}"
                )
                return text
                
        except Exception as e:
            logging.error(f"Translation failed: {str(e)}")
            raise RuntimeError("Failed to translate text")

# Singleton instance
ai_service = AIService()

def generate_description(product_data, language='en'):
    """Public interface for description generation"""
    return ai_service.generate_description(product_data, language)

def translate_text(text, source_lang, target_lang):
    """Public interface for text translation"""
    return ai_service.translate_text(text, source_lang, target_lang)