from ultralytics import YOLO

class Proctoring:
    """
    Checks if a person uses mobile phone, not in the frame
    or there are more than one people
    """
    def __init__(self, path):
        self.model = YOLO('yolov8x.pt')
        self.path = path

    def is_cheating(self) -> None:
        """
        Prints if a person is cheating
        """
        results = self.model(self.path, conf=0.1)
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

        if people_count == 0:
            flag = 1
            print("Нет человека на изображении!")
        if phone_detected:
            flag = 1
            print("Телефон в руках обнаружен!")
        if people_count > 1:
            flag = 1
            print("Много людей в кадре!")
        if flag == 0:
            print("Всё в порядке.")

if __name__ == "__main__":
    # testing
    # pr = Proctoring("two_ppl_w_phones.png")
    # pr.is_cheating()
    pass