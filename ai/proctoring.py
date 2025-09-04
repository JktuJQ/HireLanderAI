from ultralytics import YOLO

from PIL import Image
from enum import Enum


class SuspicionLevel(Enum):
    """Enum that describes proctor concerns about interviewee."""

    NORMAL = 0
    SLIGHTLY_SUSPICIOUS = 1
    SUSPICIOUS = 2
    ALERT = 3


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

    def __init__(self):
        self.model = YOLO('yolo11x.pt')
        self.model_masks = YOLO('models/masks_model.pt')

    def analyze(self, image: Image, timecode: int) -> (SuspicionLevel, str):
        """
        Analyzes image of the interviewee and detects anomalies of his behaviour.

        :param image: Image of the interviewee
        :param timecode: Timecode of the image

        :returns: Current concerns of the proctor - suspicion level and reasoning for it.
        """

        results = self.model.predict(source=image, conf=0.25, verbose=False)
        results_mask = self.model_masks(source=image, conf=0.5, verbose=False)
        phone_detected = False
        people_count = 0
        flag = 0

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                label = result.names[cls]

                if label == 'person':
                    people_count += 1
                if label == 'cell phone':
                    phone_detected = True

        mask_detected = results_mask[0].names[int(results_mask[0].boxes[0].cls[0])] == "with_mask"

        if people_count == 0:
            flag = 1
            print("Нет человека на изображении!")
        if phone_detected:
            flag = 1
            print("Телефон в руках обнаружен!")
        if people_count > 1:
            flag = 1
            print("Много людей в кадре!")
        if mask_detected:
            flag = 1
            print("Попросите снять маску!")
        if flag == 0:
            print("Всё в порядке.")
        return SuspicionLevel.NORMAL, ""
