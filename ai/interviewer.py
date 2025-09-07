from globals import *
from gtts import gTTS
import pygame
import io


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
    def text_to_speech_online(text):
        """Converts speech to text in Russian"""
        tts = gTTS(text=text, lang='ru')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    # Still need to think about the API, but it seems that realtimedness complicates things a LOT.
    def process_text(text):
        print(text)

