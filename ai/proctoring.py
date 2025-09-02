from ultralytics import YOLO

class Proctoring:
    """
    Checks if a person uses mobile phone, not in the frame
    or there are more than one people
    """
    def __init__(self, path):
        self.model = YOLO('yolo11x.pt')
        self.model_masks = YOLO('masks_model.pt')
        self.path = path

    def is_cheating(self) -> None:
        """
        Prints if a person is cheating
        """
        results = self.model(self.path, conf=0.25, verbose=False)
        results_mask = self.model_masks(self.path, conf=0.5, verbose=False)
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

if __name__ == "__main__":
    # testing
    # pr = Proctoring("mask.png")
    # pr.is_cheating()
    pass