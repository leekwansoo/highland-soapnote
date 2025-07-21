# File: speech_recognition_manager.py
"""
Speech recognition and dictation handling
"""
import speech_recognition as sr
import streamlit as st
from typing import Optional

class SpeechRecognitionManager:
    def __init__(self):
        """Initialize speech recognition components"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            st.write("Speech recognition initialized and calibrated")
    
    def listen_for_speech(self, timeout: int = 10, phrase_time_limit: int = 40) -> Optional[str]:
        """
        Listen for speech input and convert to text
        
        Args:
            timeout: Maximum time to wait for speech to start
            phrase_time_limit: Maximum time for a single phrase
            
        Returns:
            Recognized text or None if failed
        """
        try:
            with self.microphone as source:
                st.write("Listening... (speak now)")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            st.write("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            return text
        
        except sr.WaitTimeoutError:
            st.write("No speech detected within timeout period")
            return None
        except sr.UnknownValueError:
            st.write("Could not understand the speech")
            return None
        except sr.RequestError as e:
            st.write(f"Error with speech recognition service: {e}")
            return None
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        try:
            with self.microphone as source:
                st.write("Testing microphone... Say something!")
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio)
                st.write(f"Microphone test successful. You said: {text}")
                return True
        except Exception as e:
            st.write(f"Microphone test failed: {e}")
            return False

# ==========================================
