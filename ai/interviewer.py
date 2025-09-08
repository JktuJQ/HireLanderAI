from globals import *
from gtts import gTTS
import pygame
import io
from RealtimeSTT import AudioToTextRecorder
import threading


class Interviewer:
    """
    AI interviewer model is able to listen and speak with interviewee
    and follow some pre-determined plan of the interview,
    essentially conducting an interview by itself.

    Implementation tries to focus on prompt-tuning techniques (Tree-of-Thoughts, prompt-injection)
    for refining quality of the model.

    Performance of model is ensured by real-time Speech-to-Text conversion
    and on-the-fly inference + Text-to-Speech conversion.
    """

    def __init__(self, pretrained: bool = True):
        self.full_conversation: str = ""

        self.speech_to_text = None  # https://github.com/KoljaB/RealtimeSTT
        self.model = None  # https://huggingface.co/cointegrated/rubert-tiny
        self.text_to_speech = None  # https://github.com/KoljaB/RealtimeTTS
        # https://github.com/KoljaB/RealtimeSTT/blob/master/tests/minimalistic_talkbot.py

    @staticmethod
    def text_to_speech_online(text: str):
        """Converts text to speech in Russian"""
        tts = gTTS(text=text, lang='ru')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        # return fp.getvalue()

        # pygame.mixer.init()
        # pygame.mixer.music.load(fp)
        # pygame.mixer.music.play()
        # while pygame.mixer.music.get_busy():
        #     pygame.time.Clock().tick(10)

        return fp.getvalue()

    # Still need to think about the API, but it seems that realtimedness complicates things a LOT.
    def process_text(text):
        print(text)


class STTProcessor:
    def __init__(self):
        import logging
        
        logging.getLogger("faster_whisper").setLevel(logging.ERROR) # Remove annoying debug info of RealtimeSTT

        self.recorder_config = {
            "spinner": True,
            "use_microphone": False,
            "language": "ru",
            "silero_sensitivity": 1.,
            "webrtc_sensitivity": 2,
            "min_length_of_recording": 0,        
            "min_gap_between_recordings": 0,                
            "enable_realtime_transcription": True,
            "realtime_processing_pause": 0.,
            "debug_mode": False
        }
        self.recorder = AudioToTextRecorder(**self.recorder_config)
        self.recorder.start()
        self.transcribed = False
        print("STTProcessor created!")
        
    def feed_audio(self, audio_data: bytes):
        self.recorder.feed_audio(audio_data)
            
    def start_processing(self):
        self.thread = threading.Thread(target=self._process_audio, daemon=True)
        self.thread.start()
        
    def _process_audio(self):
        while True:
            text = self.recorder.text()
            if text.strip():
                self.transcribed = True
                self.text = text.strip()
                print(f"Transcribed: {text.strip()}")