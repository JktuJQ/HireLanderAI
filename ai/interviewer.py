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

    # Still need to think about the API, but it seems that realtimedness complicates things a LOT.
