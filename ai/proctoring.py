from ultralytics import YOLO

class Proctoring:
    """
    Checks if a person uses mobile phone or is not in the frame
    """
    def __init__(self, path):
        self.model = YOLO('yolov8x.pt')
        self.path = path

    def is_cheating(self) -> None:
        """
        Prints if a person is cheating
        """
        results = self.model(self.path, conf=0.1)
        person_detected = False
        phone_detected = False

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                label = result.names[cls]

                if label == 'person':
                    person_detected = True
                elif label == 'cell phone':
                    phone_detected = True

        if not person_detected:
            print("Нет человека на изображении!")
        if person_detected and phone_detected:
            print("Телефон в руках обнаружен!")
        else:
            print("Всё в порядке.")

if __name__ == "__main__":
    # testing
    # pr = Proctoring("fjsdkljflksd.png")
    # pr.is_cheating()
    pass