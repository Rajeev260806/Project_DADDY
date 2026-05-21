import pyttsx3
from loguru import logger

SPEECH_RATE = 165
SPEECH_VOLUME = 1.0
VOICE = "male"

class SpeechOutput:
    def __init__(self):
        logger.success("TTS model loaded successfully!")

    def configureModel(self):
        engine = pyttsx3.init()
        engine.setProperty("rate",SPEECH_RATE)
        engine.setProperty("volume",SPEECH_VOLUME)
        self.setVoice(engine,VOICE)
        return engine

    def setVoice(self,engine,gender: str):
        voices = engine.getProperty("voices")
        for voice in voices:
            if gender.lower() in voice.name.lower():
                engine.setProperty("voice",voice.id)
                logger.info(f"Voice Selected: {voice.name}")
                return
        if voices:
            engine.setProperty("voice", voices[0].id)
            logger.warning(f"Gender '{gender}' not found. Using: {voices[0].name}")

    def speak(self,text:str):
        if not text or not text.strip():
            return
        logger.debug(f"Speaking: {text[:80]}...")

        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            print(f"[TTS Error] Could not speak: {e}")
    
    def list_voices(self):
        engine = self.configureModel()
        voices = engine.getProperty("voices")
        print("\nAvailable voices on your system:")
        for i, voice in enumerate(voices):
            print(f"  [{i}] {voice.name} — {voice.id}")
        engine.stop()
