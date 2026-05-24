import sounddevice as sd
import numpy as np
import tempfile
import wave
import os
from faster_whisper import WhisperModel
from loguru import logger

WAKEWORD = "Hey Daddy"
SAMPLERATE = 16000
CHANNELS = 1
CHUNK_DUR = 2
SILENCE = 500

class WakeWordDetector:
    
    def __init__(self):
        logger.info("Whisper model loading for wakeword detection!")
        self.model = WhisperModel("tiny",device="cpu",compute_type="int8")
        self.wake_word = WAKEWORD.lower().strip()
        logger.success("Whisper model for wakeword detection loaded successfully!")

    def recordChunk(self) -> np.ndarray:
        audio = sd.rec(int(SAMPLERATE*CHUNK_DUR),channels=CHANNELS,samplerate=SAMPLERATE,dtype="int16")
        sd.wait()
        logger.info("Recording complete.")
        return audio

    def isLoud(self,audio: np.ndarray)->bool:
        rms = np.sqrt(np.mean(audio.astype(np.float32)**2))
        return rms>SILENCE
    
    def saveChunk(self,audio: np.ndarray):
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLERATE)
            wf.writeframes(audio.tobytes())
        return tmp.name
    
    def transcribeChunk(self, wav_path: str) -> str:
        segments, _ = self.model.transcribe(
            wav_path,
            language="en",
            beam_size=1,           
            vad_filter=True,       
        )
        text = " ".join([seg.text.strip() for seg in segments])
        return text.lower().strip()
    
    def containWakeWord(self,text:str):
        text = text.lower().strip()
        if len(text)<6:
            return False
        if self.wake_word not in text:
            return False
        return True
    
    def listen(self) -> bool:
        audio = self.recordChunk()

        if not self.isLoud(audio):
            return False
        
        wav_path = self.saveChunk(audio)
        try:
            text = self.transcribeChunk(wav_path)
            if text:
                logger.debug(f"Wake word check heard: '{text}'")

            if self.containWakeWord(text):
                logger.success(f"Wake word detected in: '{text}'")
                return True
        finally:
            os.remove(wav_path)
        return False
    
    def adjust_threshold(self, new_threshold: int):
        global SILENCE
        SILENCE = new_threshold
        logger.info(f"Silence threshold updated to: {new_threshold}")
