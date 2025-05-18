"""
Speech Interface Module for PAN (Cross-Platform)

This module provides text-to-speech and speech recognition capabilities for PAN.
On Windows, it uses SAPI5 directly for maximum stability. On Linux, it uses espeak.
For speech recognition, it uses Google Speech API by default and falls back to VOSK (offline).
"""

import speech_recognition as sr
import threading
import queue
import time
import traceback
import platform
from pan_emotions import pan_emotions
from pan_config import DEFAULT_VOICE_RATE, DEFAULT_VOICE_VOLUME
import win32com.client  # For SAPI5 on Windows
from vosk import Model, KaldiRecognizer
import json
import os

# Detect OS
is_windows = platform.system().lower() == "windows"
is_linux = platform.system().lower() == "linux"

# Path to the VOSK model (adjust to your directory)
VOSK_MODEL_PATH = "vosk_model"

# Voice parameters for different emotional states
emotion_voices = {
    'happy': {'rate': 0, 'volume': DEFAULT_VOICE_VOLUME + 0.1},
    'neutral': {'rate': 0, 'volume': DEFAULT_VOICE_VOLUME},
    'sad': {'rate': -1, 'volume': DEFAULT_VOICE_VOLUME - 0.2},
    'angry': {'rate': 1, 'volume': DEFAULT_VOICE_VOLUME + 0.1}
}

class SpeakManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self._init_engine()
        self.interrupt_speaking = threading.Event()  # Interrupt Event for stopping speech

    def _init_engine(self):
        print("[SpeakManager] Initializing TTS engine...")
        if is_windows:
            self.engine = win32com.client.Dispatch("SAPI.SpVoice")
            print("[SpeakManager] Using SAPI5 (Windows)")
        elif is_linux:
            import pyttsx3
            self.engine = pyttsx3.init(driverName='espeak')
            print("[SpeakManager] Using espeak (Linux)")

    def set_voice_by_mood(self, mood=None):
        """Adjust TTS voice settings based on mood."""
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices['neutral'])

        if is_windows:
            # SAPI5 Rate (-2 to +2) - Stable range
            scaled_rate = max(-2, min(2, settings['rate']))
            self.engine.Rate = scaled_rate
            self.engine.Volume = int(settings['volume'] * 100)
            print(f"[SpeakManager] SAPI5 Rate (Corrected): {self.engine.Rate}, Volume: {self.engine.Volume}")
        
        elif is_linux:
            # espeak (150 for natural speed)
            adjusted_rate = int(150 + (settings['rate'] * 10))
            self.engine.setProperty('rate', adjusted_rate)
            self.engine.setProperty('volume', settings['volume'])
            print(f"[SpeakManager] espeak Rate: {adjusted_rate}, Volume: {settings['volume']}")

    def speak(self, text, mood_override=None):
        """Queue text for speaking."""
        self.queue.put((text, mood_override or pan_emotions.get_mood()))

    def stop(self):
        """Immediately stop any ongoing speech."""
        self.interrupt_speaking.set()  # Trigger interrupt event
        with self.lock:
            if is_windows:
                self.engine.Speak("", 3)  # SAPI5: Immediate stop
            elif is_linux:
                self.engine.stop()       # espeak: Immediate stop
        print("[SpeakManager] Speech interrupted.")

    def _worker(self):
        """TTS Worker Thread - Continuous Processing"""
        while True:
            text, mood = self.queue.get()
            self.interrupt_speaking.clear()  # Reset interrupt flag
            try:
                self._speak_with_recovery(text, mood)
            except Exception as e:
                print(f"[TTS ERROR] Fatal Error in TTS Worker: {e}")
                traceback.print_exc()
                self._init_engine()  # Re-initialize on failure
            finally:
                self.queue.task_done()

    def _speak_with_recovery(self, text, mood):
        """Speak with Automatic Recovery and Interruptibility"""
        with self.lock:
            self.set_voice_by_mood(mood)
            print(f"[SpeakManager] Speaking with mood: {mood}")

            if is_windows:
                self.engine.Speak(text)
            elif is_linux:
                self.engine.say(text)
                self.engine.runAndWait()


# Global instance of SpeakManager
speak_manager = SpeakManager()

def speak(text, mood_override=None):
    """Public function to speak text."""
    speak_manager.speak(text, mood_override)

def stop_speaking():
    """Public function to immediately stop speaking."""
    speak_manager.stop()

def listen_to_user(timeout=5, phrase_time_limit=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Processing audio...")
            text = recognizer.recognize_google(audio)
            print(f"You said (Google): {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return None
