import sounddevice as sd
import numpy as np
import tempfile
import os
import wave
from faster_whisper import WhisperModel
from loguru import logger

MODEL_SIZE = "base"
RECORD_SECONDS = 5
SAMPLE_RATE = 16000
CHANNELS = 1

class SpeechInput:
    
    def __init__(self):
        logger.info(f"Loading Whisper model: {MODEL_SIZE}")
        self.model = WhisperModel(MODEL_SIZE,device="cpu",compute_type="int8")
        logger.success(f"Whisper model {MODEL_SIZE} loaded successfully!")

    def record_audio(self,record_sec: int = RECORD_SECONDS) -> np.ndarray:
        logger.info(f"Recording for {record_sec} seconds")
        print(f"\nRecording starts... Listening...(for {record_sec} seconds)")

        audio = sd.rec(
            int(record_sec*SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype = "int16"
        )
        sd.wait()
        logger.info("Recording complete.")
        return audio
    
    def save_temp_wav(self, audio: np.ndarray) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)         # 2 bytes = 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        return tmp.name

    def transcribe(self,audio_path:str) -> str:
        segments,info = self.model.transcribe(
            audio_path,
            language = "en",
            beam_size = 5,
            vad_filter = True,
        )

        text = " ".join([seg.text.strip() for seg in segments])
        logger.debug(f"Transcribed: {text}")
        return text.strip()
    
    def listen(self,record_sec: int = RECORD_SECONDS) -> str:
        audio = self.record_audio(record_sec)
        file_audio = self.save_temp_wav(audio)
        try:
            text = self.transcribe(file_audio)
        finally:
            os.remove(file_audio)
        return text
