import streamlit as st
import audio_recorder_streamlit as audio_recorder
import requests
import io
import os
import time
from datetime import datetime

class VoiceInput:
    """Handles voice recording and speech-to-text conversion"""
    
    def __init__(self, language='en'):
        self.language = language
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
        self.audio_bytes = None
        self.last_recording_time = None
    
    def _save_audio(self, audio_bytes):
        """Save audio to session state for playback"""
        if audio_bytes:
            self.audio_bytes = audio_bytes
            self.last_recording_time = datetime.now()
            return True
        return False
    
    def _process_recording(self):
        """Send audio to backend for speech processing"""
        if not self.audio_bytes:
            return None
            
        try:
            # Create in-memory file
            audio_stream = io.BytesIO(self.audio_bytes)
            audio_stream.name = "recording.wav"
            
            # Prepare request
            files = {'audio': audio_stream}
            data = {'language': self.language}
            
            # Show processing status
            with st.spinner("Processing voice..."):
                response = requests.post(
                    f"{self.backend_url}/api/speech/process",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()['text']
                else:
                    st.error("Voice processing failed")
                    return None
                    
        except requests.exceptions.Timeout:
            st.error("Voice processing timed out")
            return None
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return None
    
    def render(self):
        """Render the voice input interface"""
        st.write("Click the microphone to record:")
        
        # Record audio
        audio_bytes = audio_recorder.audio_recorder(
            text="",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=2.0,
            sample_rate=44100,
        )
        
        # Save new recordings
        if audio_bytes and audio_bytes != self.audio_bytes:
            self._save_audio(audio_bytes)
        
        # Show audio player if recording exists
        if self.audio_bytes:
            st.audio(self.audio_bytes, format="audio/wav")
            
            # Automatic processing after 2 seconds of silence
            if self.last_recording_time and (datetime.now() - self.last_recording_time).total_seconds() > 2:
                return self._process_recording()
        
        return None