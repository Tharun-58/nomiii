import os
import io
import logging
from google.cloud import speech_v1p1beta1 as speech
from google.api_core.exceptions import GoogleAPICallError
import config

class SpeechProcessor:
    """Handles speech-to-text conversion using Google Cloud Speech API"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Google Cloud Speech client"""
        try:
            if config.GOOGLE_CREDENTIALS_PATH and os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
                self.client = speech.SpeechClient.from_service_account_json(
                    config.GOOGLE_CREDENTIALS_PATH
                )
                logging.info("Google Speech client initialized successfully")
            else:
                logging.error("Google credentials path not configured or invalid")
                raise RuntimeError("Google Cloud credentials not available")
        except Exception as e:
            logging.error(f"Failed to initialize speech client: {str(e)}")
            raise

    def process_audio(self, audio_file, language_code='en-IN'):
        """
        Convert speech audio to text
        
        Args:
            audio_file: File-like object containing audio data
            language_code: BCP-47 language code (e.g., 'en-IN', 'hi-IN')
            
        Returns:
            str: Transcribed text
        """
        try:
            # Validate input
            if not audio_file:
                raise ValueError("No audio file provided")
                
            if not self.client:
                raise RuntimeError("Speech client not initialized")
                
            # Read audio content
            content = audio_file.read()
            if not content:
                raise ValueError("Empty audio file")
                
            logging.info(f"Processing audio for language: {language_code}")
            
            # Configure recognition
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='default',
                use_enhanced=True,
                enable_word_confidence=True,
                metadata=speech.RecognitionMetadata(
                    interaction_type=speech.RecognitionMetadata.InteractionType.DICTATION,
                    microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
                    original_media_type=speech.RecognitionMetadata.OriginalMediaType.AUDIO,
                    recording_device_type=speech.RecognitionMetadata.RecordingDeviceType.SMARTPHONE
                )
            )
            
            # Perform speech recognition
            logging.debug("Sending request to Google Speech API")
            response = self.client.recognize(config=config, audio=audio)
            
            # Process results
            transcript = ''
            for result in response.results:
                transcript += result.alternatives[0].transcript + '\n'
                
            transcript = transcript.strip()
            logging.info(f"Speech recognition successful. Transcript: {transcript[:100]}...")
            
            return transcript
            
        except GoogleAPICallError as e:
            logging.error(f"Google API error: {str(e)}", exc_info=True)
            raise RuntimeError("Speech recognition service unavailable")
        except Exception as e:
            logging.error(f"Speech processing failed: {str(e)}", exc_info=True)
            raise

# Singleton instance
speech_processor = SpeechProcessor()

def process_audio(audio_file, language_code='en-IN'):
    """Public interface for speech processing"""
    return speech_processor.process_audio(audio_file, language_code)