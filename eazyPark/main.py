# eazyPark/main.py

import cv2
import time
from datetime import datetime

from eazyPark.camera import CameraCapture
from eazyPark.detection import detect_cars
from eazyPark.zones import (
    ZONES, add_zone, remove_zone, draw_zones, bbox_in_zone,
    point_in_zone, load_zones_from_file, save_zones_to_file
)
from eazyPark.network import send_zone_status
from eazyPark.config import (
    CAMERA_NAME, CAMERA_COUNTRY, CAMERA_REGION, CAMERA_CITY,
    CAMERA_STREET, CAMERA_COORDS
)

# ------------------- Глобальные переменные -------------------
zone_status = {}               # Хранит текущий статус зон: { "zone_0": bool, ... }
drawing_zone = False
removing_zone = False
current_zone_points = []
AUTO_SEND_INTERVAL = 60  # Интервал (секунды) для массовой отправки статусов (можно менять)
last_auto_send_time = 0  # Когда в последний раз отсылали статусы "скопом"

# ------------------- Инициализация статусов -------------------
def init_zone_status():
    """
    Создаёт словарь zone_status с False (свободна) для каждой зоны при запуске,
    если ещё нет записи. Иначе оставляем текущие значения.
    """
    for i, _zone in enumerate(ZONES):
        zone_id = f"zone_{i}"
        if zone_id not in zone_status:
            zone_status[zone_id] = False

# ------------------- Логирование -------------------
def log_zone_change(zone_id, old_status, new_status):
    """
    Записывает в текстовый файл момент изменения статуса зоны.
    Формат: 2023-10-02 12:34:56: Zone zone_1 changed from free to busy
    """
    old_str = "busy" if old_status else "free"
    new_str = "busy" if new_status else "free"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("zone_changes.log", "a", encoding="utf-8") as f:
        f.write(f"{timestamp}: Zone {zone_id} changed from {old_str} to {new_str}\n")


# ------------------- Мышиные колбэки -------------------
def mouse_callback(event, x, y, flags, param):
    global drawing_zone, removing_zone, current_zone_points

    if drawing_zone:
        if event == cv2.EVENT_LBUTTONDOWN:
            current_zone_points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Заканчиваем добавление зоны
            if len(current_zone_points) > 2:
                add_zone(current_zone_points.copy())
                save_zones_to_file()
                print(f"Новая зона добавлена: {current_zone_points}")
                new_index = len(ZONES) - 1
                zone_id = f"zone_{new_index}"
                zone_status[zone_id] = False
            current_zone_points.clear()
            drawing_zone = False

    elif removing_zone:
        if event == cv2.EVENT_LBUTTONDOWN:
            zone_index = find_zone_index_by_point(x, y)
            if zone_index is not None:
                print(f"Удаляем зону №{zone_index} : {ZONES[zone_index]}")
                remove_zone(zone_index)
                save_zones_to_file()
            removing_zone = False

def find_zone_index_by_point(x, y):
    """
    Ищет индекс зоны, в которую попадает точка (x, y).
    Возвращает None, если точка не попала ни в одну зону.
    """
    for i, zone_points in enumerate(ZONES):
        if point_in_zone(x, y, zone_points):
            return i
    return None

# ------------------- Подсчёт свободных зон -------------------
def count_free_spots(detections, zones):
    """
    Возвращает (кол-во_свободных_зон, множество_индексов_занятых).
    """
    used_zones = set()
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        for i, zone_points in enumerate(zones):
            if bbox_in_zone((x1, y1, x2, y2), zone_points):
                used_zones.add(i)
    free_count = len(zones) - len(used_zones)
    return free_count, used_zones

# ------------------- Рисование зон с учётом статуса -------------------
def draw_zones_colored(frame):
    """
    Вместо стандартного draw_zones - рисует зоны цветом,
    зависящим от статуса:
      - красный (0,0,255), если зона занята
      - зелёный (0,255,0), если свободна
    Также пишет текст: "zone_i (busy/free)" возле полигона.
    """
    for i, zone_points in enumerate(ZONES):
        zone_id = f"zone_{i}"
        is_busy = zone_status.get(zone_id, False)

        # Выбираем цвет
        color = (0, 0, 255) if is_busy else (0, 255, 0)  # BGR

        # Преобразуем в NumPy для полилинии
        import numpy as np
        pts = np.array(zone_points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

        # Рисуем подпись около центра многоугольника
        cx, cy = get_polygon_center(zone_points)
        status_str = "busy" if is_busy else "free"
        text = f"zone_{i} ({status_str})"
        cv2.putText(frame, text, (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def get_polygon_center(points):
    """
    Возвращает (cx, cy) - приблизительный центр многоугольника.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    cx = int(sum(xs) / len(xs))
    cy = int(sum(ys) / len(ys))
    return (cx, cy)

# ------------------- Массовая отправка статусов всех зон -------------------
def send_all_zones_status():
    """
    Проходит по всему zone_status и отправляет на сервер текущее состояние.
    """
    for i, _ in enumerate(ZONES):
        zone_id = f"zone_{i}"
        is_busy = zone_status.get(zone_id, False)
        send_zone_status(
            spot_id=zone_id,
            is_busy=is_busy,
            camera_name=CAMERA_NAME,
            country=CAMERA_COUNTRY,
            region=CAMERA_REGION,
            city=CAMERA_CITY,
            street=CAMERA_STREET,
            coords=CAMERA_COORDS
        )
    print("[AUTO-SEND] Отправили статусы всех зон на сервер.")

# ------------------- Основная функция -------------------
def main():
    print("[INFO] Запуск eazyPark...")
    camera = CameraCapture()
    if not camera.cap.isOpened():
        print("[ERROR] Камера не открыта. Завершение...")
        return

    cv2.namedWindow("eazyPark")
    cv2.setMouseCallback("eazyPark", mouse_callback)

    # 1) Загружаем зоны и создаём zone_status
    print("[INFO] Загружаем зоны из файла...")
    load_zones_from_file()
    init_zone_status()

    global last_auto_send_time

    print("[INFO] Начинаем цикл обработки кадров.")
    try:
        while True:
            ret, frame = camera.get_frame()
            if not ret:
                print("[WARNING] Кадр не получен. Ждём 1с.")
                time.sleep(1)
                continue

            # Рисуем "промежуточные" линии зоны (когда рисуем новую)
            for i in range(len(current_zone_points) - 1):
                cv2.line(frame, current_zone_points[i], current_zone_points[i + 1],
                         (0, 0, 255), 2)
            for p in current_zone_points:
                cv2.circle(frame, p, 5, (0, 0, 255), -1)

            # Вместо обычного draw_zones() используем цветное
            draw_zones_colored(frame)

            # Детектим машины
            detections = detect_cars(frame)

            # Считаем, сколько в зонах машин
            free_count, used_zones = count_free_spots(detections, ZONES)
            count_in_zone = len(used_zones)

            # Пробегаемся по детекциям, рисуем их
            for det in detections:
                x1, y1, x2, y2 = det["bbox"]
                conf = det["confidence"]
                cls_name = det["class"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{cls_name} {conf:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # Если попал в зону, перекрашиваем bbox
                for i_zone, zone_points in enumerate(ZONES):
                    if bbox_in_zone((x1, y1, x2, y2), zone_points):
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        break

            # Обновляем zone_status и отправляем статус ИЛИ логируем изменение
            for i, _zone_points in enumerate(ZONES):
                zone_id = f"zone_{i}"
                was_busy = zone_status[zone_id]
                now_busy = (i in used_zones)
                if was_busy != now_busy:
                    # Логируем изменение
                    log_zone_change(zone_id, was_busy, now_busy)

                    # Сохраняем новый статус
                    zone_status[zone_id] = now_busy

                    # Отправляем сразу же
                    send_zone_status(
                        spot_id=zone_id,
                        is_busy=now_busy,
                        camera_name=CAMERA_NAME,
                        country=CAMERA_COUNTRY,
                        region=CAMERA_REGION,
                        city=CAMERA_CITY,
                        street=CAMERA_STREET,
                        coords=CAMERA_COORDS
                    )

            # Выводим информацию поверх кадра
            cv2.putText(frame, f"Detections: {len(detections)}, In zone: {count_in_zone}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, f"Free spots: {free_count}",
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            # Показываем кадр
            cv2.imshow("eazyPark", frame)

            # ------------------- Автоотправка каждые X секунд -------------------
            current_time = time.time()
            if current_time - last_auto_send_time > AUTO_SEND_INTERVAL:
                send_all_zones_status()
                last_auto_send_time = current_time
            # --------------------------------------------------------------------

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('z'):
                global drawing_zone, removing_zone
                drawing_zone = True
                removing_zone = False
                print("[INFO] Режим рисования зоны (ЛКМ - точки, ПКМ - завершить).")
            elif key == ord('d'):
                drawing_zone = False
                removing_zone = True
                print("[INFO] Режим удаления зоны (ЛКМ по зоне - удалить).")

    except KeyboardInterrupt:
        print("[INFO] Остановлено пользователем (Ctrl+C).")

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
