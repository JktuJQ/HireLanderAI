from globals import *
from gtts import gTTS
# import pygame
import io
from RealtimeSTT import AudioToTextRecorder
import threading

from mistralai import Mistral
import os


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
    @staticmethod
    def process_text(question, answer, previous=None):
        api_key = SECRETS["INTERVIEWER_MODEL_API_KEY"]
        model = "mistral-large-latest"

        client = Mistral(api_key=api_key)

        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content":
                        f"""Ты – виртуальный рекрутер, проводящий онлайн-собеседование. Тебе на вход подаётся:\n
                        Вопрос в формате:\n
                        '      критерий: <текст критерия из входа>,\n'
                        '      вопрос: <вопрос для кандидата>,\n'
                        '      тип: <behavioral|technical|education|culture|other>,\n'
                        '      сложность: <easy|medium|hard>,\n'
                        '      follow_ups: [<вопрос 1>, <вопрос 2>]\n'
                        сам вопрос: {question}\n
                        ответ кандидата: {answer}\n
                        предыдущий диалог: {previous}\n
                        
                        Твоя задача:\n
                        Оценить ответ кандидата:\n                        
                        Проверить, насколько он соответствует критерию.\n                        
                        Отметить, если информация слишком общая, неполная или не соответствует ожиданиям.\n                        
                        Продолжить диалог:\n                        
                        Если ответ требует уточнения или углубления — задай один дополнительный вопрос:\n                        
                        либо выбери подходящий из списка follow_ups,\n                        
                        либо придумай свой релевантный вопрос, если готовые не подходят.\n                        
                        Старайся поддерживать вежливый и профессиональный тон.\n                        
                        Завершить обсуждение вопроса:\n
                        
                        Если ответ полный и не требует уточнений, или предыдущий диалог слишком долгий, выдай специальный сигнал:\n
                        [NEXT_QUESTION]\n
                        
                        Формат выхода:\n

                        Если нужен дополнительный вопрос → ТОЛЬКО реплика рекрутера (одно-два предложения/вопрос).\n
                        Твой комментарий или оценка НЕ НУЖНЫ, тебе надо только выдать реплику, которую рекрутер зачитает вслух.\n
                        
                        Если переход к следующему вопросу → ровно строка [NEXT_QUESTION].
                        """,
                },
            ]
        )
        print(chat_response.choices[0].message.content)


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

if __name__ == "__main__":
    q = """критерий: высшее техническое или экономическое образование\n тип: education\n сложность: easy\n follow_ups: ["какие курсы или сертификаты вы получали во время учебы?", "как ваше образование связано с работой бизнес аналитика?"]"""
    ans = "да хрен его знает"
    Interviewer.process_text(q, ans)