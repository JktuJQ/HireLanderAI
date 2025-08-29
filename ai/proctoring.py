from enum import Enum

from PIL import Image


class SuspicionLevel(Enum):
    """Enum that describes proctor concerns about interviewee."""

    NORMAL = 0
    SLIGHTLY_SUSPICIOUS = 1
    SUSPICIOUS = 2
    VERY_SUSPICIOUS = 3


class Proctor:
    """
    Proctor for the interview that is trained to detect anomalies of interviewee behaviour and report it.

    Proctor implements something like clever state machine,
    which is able to distinguish one-off suspicious movement from consistent.
    For example, if person only ever does something suspicion and
    after than system is not detecting any anomalies for a long time,
    then suspicion level is dropped.
    Something similar also happens if person frequently behaves suspicious.
    """

    def __init__(self, pretrained: bool = True):
        self.last_suspicious_timecode = None
        self.suspicion_level = SuspicionLevel.NORMAL

        self.model = None  # https://pypi.org/project/proctoring/

    def analyze(self, image: Image, timecode: int) -> SuspicionLevel:
        """
        Analyzes image of the interviewee and detects anomalies of his behaviour.

        :param image: Image of the interviewee
        :param timecode: Timecode of the image

        :returns: Current concerns of the proctor
        """

        return self.suspicion_level
