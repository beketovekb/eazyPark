# eazyPark/camera.py

import cv2
from eazyPark.config import RTSP_URL

class CameraCapture:
    def __init__(self, source=RTSP_URL):
        self.source = source
        # Инициализируем видеокапчер OpenCV
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print(f"[ERROR] Не удалось открыть поток: {self.source}")

    def get_frame(self):
        """
        Считывает один кадр и возвращает (ret, frame).
        ret = True/False
        frame = numpy array
        """
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            return ret, frame
        return False, None

    def release(self):
        """
        Освобождает ресурсы видеокапчера
        """
        if self.cap.isOpened():
            self.cap.release()
