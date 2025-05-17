import pyttsx3
import speech_recognition as sr
import threading
import queue
import time
import traceback
from pan_emotions import pan_emotions

try:
    import win32com.client
    has_sapi = True
except ImportError:
    has_sapi = False

emotion_voices = {
    'happy': {'rate': 180, 'volume': 1.0},
    'excited': {'rate': 200, 'volume': 1.0},
    'neutral': {'rate': 160, 'volume': 0.9},
    'sad': {'rate': 140, 'volume': 0.7},
    'angry': {'rate': 200, 'volume': 1.0},
    'scared': {'rate': 130, 'volume': 0.6},
    'calm': {'rate': 150, 'volume': 0.8},
    'curious': {'rate': 170, 'volume': 0.9},
}

MAX_CHUNK_LENGTH = 150

class SpeakManager:
    def __init__(self):
        self._init_engine()
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.speech_count = 0
        self.speaking_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

        if has_sapi:
            self.sapi_engine = win32com.client.Dispatch("SAPI.SpVoice")
        else:
            self.sapi_engine = None

    def _init_engine(self):
        print("[SpeakManager] Initializing pyttsx3 engine")
        self.engine = pyttsx3.init()

    def set_voice_by_mood(self, mood=None):
        if not mood:
            mood = pan_emotions.get_mood()
        settings = emotion_voices.get(mood, emotion_voices['neutral'])
        self.engine.setProperty('rate', settings['rate'])
        self.engine.setProperty('volume', settings['volume'])

    def _chunk_text(self, text):
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= MAX_CHUNK_LENGTH:
                current += (sentence + " ")
            else:
                chunks.append(current.strip())
                current = sentence + " "
        if current:
            chunks.append(current.strip())
        return chunks

    def _speak_chunk(self, chunk, mood):
        if self.sapi_engine:
            try:
                print("[SpeakManager] Using Windows SAPI for TTS chunk.")
                self.sapi_engine.Speak(chunk)
                return
            except Exception as e:
                print(f"SAPI TTS failed: {e}")
        try:
            self.set_voice_by_mood(mood)
            self.engine.say(chunk)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS error in chunk: {e}")
            traceback.print_exc()

    def _worker(self):
        while True:
            text, mood = self.queue.get()
            try:
                with self.lock:
                    self.engine.stop()
                    self._init_engine()

                    print("[SpeakManager] Speaking started")
                    self.speaking_event.set()

                    chunks = self._chunk_text(text)
                    for chunk in chunks:
                        self._speak_chunk(chunk, mood)
                        time.sleep(0.05)

                    self.speech_count += 1
                    print("[SpeakManager] Speaking ended")

            except Exception:
                print("TTS error occurred in worker:")
                traceback.print_exc()
            finally:
                self.speaking_event.clear()
            self.queue.task_done()

    def speak(self, text, mood_override=None):
        self.queue.put((text, mood_override))

speak_manager = SpeakManager()

def speak(text, mood_override=None):
    speak_manager.speak(text, mood_override)

def warn_low_affinity(user_id):
    # Placeholder example: return a warning string if affinity low, else empty
    affinity = get_affinity(user_id)
    if affinity < -5:  # example threshold
        return "Warning: I don't trust you much."
    return ""


def listen_to_user(timeout=5):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        try:
            audio = recognizer.listen(source, timeout=timeout)
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start")
            return None
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return None
