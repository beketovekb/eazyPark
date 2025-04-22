# eazyPark/zones.py
import cv2
import numpy as np
from shapely.geometry import Point, Polygon

ZONES = []

def add_zone(zone_points):
    ZONES.append(zone_points)

def remove_zone(index):
    """Удаляет зону из списка ZONES по индексу."""
    if 0 <= index < len(ZONES):
        ZONES.pop(index)

def draw_zones(frame):
    for zone in ZONES:
        # Преобразуем список [(x1, y1), (x2, y2), ...] в NumPy массив
        pts = np.array(zone, dtype=np.int32)  # shape (N, 2)
        pts = pts.reshape((-1, 1, 2))         # shape (N, 1, 2)

        # Теперь cv2.polylines может обработать
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)

def bbox_in_zone(bbox, zone_points):
    (bx1, by1, bx2, by2) = bbox
    # Простейший вариант — проверяем центр bbox
    cx = (bx1 + bx2) / 2
    cy = (by1 + by2) / 2

    polygon = Polygon(zone_points)
    point_center = Point(cx, cy)
    return polygon.contains(point_center)

import json

def point_in_zone(x, y, zone_points):
    """Проверяем, лежит ли точка (x, y) внутри многоугольника zone_points."""
    polygon = Polygon(zone_points)
    return polygon.contains(Point(x, y))

def save_zones_to_file(filename="zones.json"):
    """
    Сохраняет ZONES в JSON-файл.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(ZONES, f)

def load_zones_from_file(filename="zones.json"):
    """
    Загружает зоны из JSON-файла в ZONES.
    """
    import os
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            # data - список зон, каждая зона - список координат
            ZONES.clear()
            ZONES.extend(data)

