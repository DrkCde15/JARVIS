import pyttsx3
import threading
import time
from queue import Queue
from typing import Callable
from commands.constants import Colors

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

class VoiceCommandSystem:
    def __init__(self):
        self.engine = self._init_voice_engine()
        self.command_queue = Queue()
        self.voice_lock = threading.Lock()
        self.is_speaking = False
        self._start_command_processor()

    def _init_voice_engine(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.9)
            return engine
        except Exception as e:
            print(f"Voice engine initialization failed: {e}")
            return None

    def _start_command_processor(self):
        def processor():
            while True:
                cmd_func, args, kwargs = self.command_queue.get()
                try:
                    time.sleep(0.3)
                    cmd_func(*args, **kwargs)
                except Exception as e:
                    print(f"Error in voice command execution: {e}")
                finally:
                    self.command_queue.task_done()
        
        thread = threading.Thread(target=processor, daemon=True)
        thread.start()

    def speak(self, text: str):
        if not self.engine:
            print(f"Voice Assistant: {text}")
            return

        def _speak():
            with self.voice_lock:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.is_speaking = False

        threading.Thread(target=_speak, daemon=True).start()

    def add_command(self, command_func: Callable, *args, **kwargs):
        self.command_queue.put((command_func, args, kwargs))

voice_system = VoiceCommandSystem()

def falar(texto: str):
    voice_system.speak(texto)


def ouvir(timeout: int = 5, phrase_time_limit: int = 10, language: str = "pt-BR"):
    """Captura uma frase pelo microfone e retorna texto transcrito."""
    if not HAS_SR:
        print("SpeechRecognition nao esta instalado.")
        return None

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        print(f"Erro ao acessar microfone: {e}")
        return None

    try:
        texto = recognizer.recognize_google(audio, language=language)
        return texto.strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Erro no servico de reconhecimento de voz: {e}")
        return None
