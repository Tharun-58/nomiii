from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from typing import Optional, Dict
import logging
from pathlib import Path
import os
import torch

class Translator:
    """
    A translation service supporting multiple Indian languages.
    Uses Helsinki-NLP models for translation tasks.
    """
    
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil", 
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati"
    }
    
    MODEL_MAPPING = {
        ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
        ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
        # Add more language pairs as needed
    }
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_cache_dir = Path(os.getenv("MODEL_CACHE_DIR", "./model_cache"))
        self._prepare_model_cache()
        
    def _prepare_model_cache(self):
        """Create model cache directory if it doesn't exist"""
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_model_key(self, source_lang: str, target_lang: str) -> Optional[str]:
        """Get the model identifier for a language pair"""
        return self.MODEL_MAPPING.get((source_lang, target_lang))
    
    def _load_model(self, model_name: str):
        """Load a translation model"""
        if model_name in self.models:
            return
            
        try:
            logging.info(f"Loading translation model: {model_name}")
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.model_cache_dir
            )
            
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=self.model_cache_dir,
                device_map="auto"
            )
            
            if self.device == "cuda":
                model = model.to(self.device)
            
            self.models[model_name] = model
            self.tokenizers[model_name] = tokenizer
            
        except Exception as e:
            logging.error(f"Failed to load translation model: {str(e)}")
            raise RuntimeError(f"Translation model {model_name} loading failed")
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text between supported languages.
        
        Args:
            text: Input text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if source_lang == target_lang:
            return text
            
        model_key = self._get_model_key(source_lang, target_lang)
        if not model_key:
            logging.warning(f"No direct model for {source_lang}->{target_lang}")
            return self._cascade_translation(text, source_lang, target_lang)
            
        self._load_model(model_key)
        
        try:
            tokenizer = self.tokenizers[model_key]
            model = self.models[model_key]
            
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = model.generate(**inputs)
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            logging.info(f"Translated: {text[:50]}... -> {translated[:50]}...")
            return translated
            
        except Exception as e:
            logging.error(f"Translation failed: {str(e)}")
            raise RuntimeError("Translation failed")
    
    def _cascade_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Handle translation through an intermediate language when direct model isn't available.
        """
        # Default cascade path: source -> English -> target
        if source_lang != "en":
            english_text = self.translate(text, source_lang, "en")
            return self.translate(english_text, "en", target_lang)
        
        # If source is English but no direct model, try via Hindi
        if target_lang in self.SUPPORTED_LANGUAGES:
            hindi_text = self.translate(text, "en", "hi")
            return self.translate(hindi_text, "hi", target_lang)
        
        raise ValueError(f"No translation path available for {source_lang}->{target_lang}")

# Singleton instance for the application
translator = Translator()

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Public interface for text translation"""
    return translator.translate(text, source_lang, target_lang)