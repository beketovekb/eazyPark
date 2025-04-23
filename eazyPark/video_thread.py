# eazyPark/video_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from eazyPark.camera import CameraCapture

class VideoThread(QThread):
    frame_ready = pyqtSignal(object)      # numpy.ndarray (BGR)

    def __init__(self):
        super().__init__()
        self.cap = CameraCapture()
        self._run = True

    def run(self):
        while self._run and self.cap.cap.isOpened():
            ok, frame = self.cap.get_frame()
            if ok:
                self.frame_ready.emit(frame)
            self.msleep(15)               # ~60 FPS

    def stop(self):
        self._run = False
        self.cap.release()
        self.wait()
