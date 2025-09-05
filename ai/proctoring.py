from enum import Enum

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from ultralytics import YOLO


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

        mask_detected = results_mask[0].names[int(
            results_mask[0].boxes[0].cls[0])] == "with_mask"

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


class GetPersonsGaze:
    """
    Gets a person's direction of view using mediapipe
    """

    def __init__(self, path):
        self.path = path
        # модель для обнаружения ключевых точек
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            refine_landmarks=True)

        self.LEFT_IRIS_IDX = [468, 469, 470, 471,
                              472]  # индексы, которые отмечают радужную оболочку левого глаза
        self.RIGHT_IRIS_IDX = [473, 474, 475, 476,
                               477]  # радужка правого глаза
        self.LEFT_EYE_CORNERS = [33, 133]  # угол левого глаза
        self.RIGHT_EYE_CORNERS = [362, 263]  # угол правого глаза
        self.TOP_IDX = 159
        self.BOTTOM_IDX = 145

    @staticmethod
    def landmarks_to_xy(landmark, w, h):
        """Переводит нормализованный landmark
        из нормализованных координат в пиксели (x,y)."""
        return np.array([landmark.x * w, landmark.y * h], dtype=np.float32)

    def eye_center_and_size(self, landmarks, corner_idx, image_w, image_h):
        """Вычисляет центр глаза и размеры по двум corner точкам."""
        p1 = landmarks[corner_idx[0]]
        p2 = landmarks[corner_idx[1]]
        p1_xy = self.landmarks_to_xy(p1, image_w, image_h)
        p2_xy = self.landmarks_to_xy(p2, image_w, image_h)
        center = (p1_xy + p2_xy) / 2.0  # середина между corner точками
        width = np.linalg.norm(p1_xy - p2_xy)  # расстояние между углами глаза
        height = width * 0.6  # самый лучший вариант, я пробовал, честно
        return center, width, height

    def iris_center(self, landmarks, iris_idx_list, image_w, image_h):
        """Находит центр радужной оболочки"""
        pts = [landmarks[i] for i in iris_idx_list]
        pts_xy = np.array(
            [self.landmarks_to_xy(p, image_w, image_h) for p in pts])
        return pts_xy.mean(
            axis=0)  # усредняем положение точек радужной оболочки

    @staticmethod
    def classify_gaze(iris_xy, eye_center, eye_w, eye_h, x_thresh=0.15,
                      y_thresh=0.12):
        """
        iris_xy, eye_center: в пикселях.
        x_thresh, y_thresh: пороги в долях от размера глаза (например 0.15 == 15% ширины глаза).
        Возвращает 'left','right','up','down','center'.
        """
        # нормированные смещения радужной оболочки
        dx = (iris_xy[0] - eye_center[0]) / eye_w
        dy = (iris_xy[1] - eye_center[1]) / eye_h

        ax = abs(dx)
        ay = abs(dy)

        if ax < x_thresh and ay < y_thresh:  # мало сместилось относительно центра
            return "center", dx, dy

        if ax >= ay:  # сместилось по оси x больше чем по y
            return ("left" if dx < 0 else "right"), dx, dy
        else:
            return ("up" if dy < 0 else "down"), dx, dy

    def estimate_gaze_from_image(self):
        """Возвращает направление взгляда по фотографии"""
        img = cv2.imread(self.path)
        if img is None:
            raise FileNotFoundError(f"Не удалось открыть {self.path}")
        h, w = img.shape[:2]
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        results = self.face_mesh.process(img_rgb)
        if not results.multi_face_landmarks:
            return {"error": "Лицо не найдено"}

        face_landmarks = results.multi_face_landmarks[0].landmark

        # получаем центры радужек
        left_iris_xy = self.iris_center(face_landmarks, self.LEFT_IRIS_IDX, w,
                                        h)
        right_iris_xy = self.iris_center(face_landmarks, self.RIGHT_IRIS_IDX,
                                         w, h)

        # получаем центры глаз и размеры
        left_eye_center, left_w, left_h = self.eye_center_and_size(
            face_landmarks,
            self.LEFT_EYE_CORNERS,
            w, h)
        right_eye_center, right_w, right_h = self.eye_center_and_size(
            face_landmarks, self.RIGHT_EYE_CORNERS, w, h)

        # классифицируем по каждому глазу
        left_dir, ldx, ldy = self.classify_gaze(left_iris_xy, left_eye_center,
                                                left_w, left_h)
        right_dir, rdx, rdy = self.classify_gaze(right_iris_xy,
                                                 right_eye_center,
                                                 right_w, right_h)

        # если оба глаза говорят одно и то же -> берем его.
        # иначе, берем более выраженное смещение (max по абсолютному значению dx/dy).
        if left_dir == right_dir:
            final = left_dir
        else:
            left_strength = max(abs(ldx), abs(ldy))
            right_strength = max(abs(rdx), abs(rdy))
            final = left_dir if left_strength >= right_strength else right_dir

        # Вернём детальную инфу для отладки
        # return {
        #     "final_gaze": final,
        #     "left": {"dir": left_dir, "dx": float(ldx), "dy": float(ldy)},
        #     "right": {"dir": right_dir, "dx": float(rdx), "dy": float(rdy)},
        #     "left_iris_xy": left_iris_xy.tolist(),
        #     "right_iris_xy": right_iris_xy.tolist(),
        #     "left_eye_center": left_eye_center.tolist(),
        #     "right_eye_center": right_eye_center.tolist()
        # }
        return final


class AntiCheat:
    """
    Checks if a person is cheating based on their gaze.
    The sliding window contains last 300 seconds of person's gaze,
    if the last 15 seconds' most common gaze differs from it,
    there is an alarm for an interviewer.
    """

    def __init__(self):
        self.long_gaze = ""
        self.gazes = []
        self.short_gaze = ""
        self.curr_time = 0

    @staticmethod
    def _get_most_popular_state(array) -> str:
        states = dict()
        states["ups"] = array.count("up")
        states["downs"] = array.count("down")
        states["lefts"] = array.count("left")
        states["rights"] = array.count("right")
        states["centers"] = array.count("center")

        most_popular = max(states.values())
        # возвращает первый ключ, значение которого равно most_popular
        return next((k for k, v in states.items() if v == most_popular), None)

    def step(self, status: str) -> None:
        self.gazes.append(status)

        if 16 <= self.curr_time:
            short_gazes = self.gazes[-15:]
            self.short_gaze = self._get_most_popular_state(short_gazes)

            if self.curr_time > 300:
                long_gazes = self.gazes[-300:]
                self.long_gaze = self._get_most_popular_state(long_gazes)
                self.gazes.pop(0)

        if self.long_gaze != self.short_gaze and self.long_gaze != "":
            print("АЛЯРМА!!!!11!!!1!! ПОДОЗРЕНИЕ НА СПИСЫВАНИЕ!11!!!!111111!!!!!!!адын")

        self.curr_time += 1
