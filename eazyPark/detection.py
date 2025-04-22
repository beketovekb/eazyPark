# eazyPark/detection.py

from ultralytics import YOLO
import torch
from .config import MODEL_PATH

# Инициализируем модель при импорте модуля (однократно)
model = YOLO(MODEL_PATH)  # Например, "models/yolov8n.pt"

# Можно настроить порог уверенности (confidence threshold) при необходимости
CONF_THRESHOLD = 0.3

def detect_cars(frame):
    """
    Запускает YOLO детектор на изображении 'frame' (OpenCV формат BGR).
    Возвращает список словарей:
    [
      {
        'bbox': (x1, y1, x2, y2),
        'confidence': 0.95,
        'class': 'car'
      },
      ...
    ]
    """

    # Выполняем предсказание
    results = model.predict(
        source=frame,        # само изображение (numpy массив)
        conf=CONF_THRESHOLD  # порог детекции
    )

    # results – обычно список из одного элемента (т.к. мы подали один frame)
    detections = []
    if len(results) > 0:
        # Берём первый элемент (первый результат)
        r = results[0]

        # Пробегаемся по всем боксам
        for box in r.boxes:
            cls_id = int(box.cls[0])       # индекс класса
            conf = float(box.conf[0])      # уверенность
            x1, y1, x2, y2 = box.xyxy[0].tolist()  # координаты bbox

            # Название класса (строка), например "car", "truck"...
            class_name = model.names.get(cls_id, "unknown")

            # Если хотим отфильтровать только машины, грузовики, автобусы (свой набор)
            if class_name in ("car", "truck", "bus"):
                detections.append({
                    "bbox": (int(x1), int(y1), int(x2), int(y2)),
                    "confidence": conf,
                    "class": class_name
                })

    return detections
