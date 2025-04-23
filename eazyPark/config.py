# eazyPark/config.py

# ------------------- Камера -------------------
CAMERA_COUNTRY = "Kazakhstan"
CAMERA_REGION = "Pavlodar region"
CAMERA_CITY = "Ekibastuz"
CAMERA_STREET = "Margulana st."
CAMERA_COORDS = "51.74697163535025, 75.31500771443974"
CAMERA_NAME = "ParkingCam"

# ------------------- Безопасность (токен) -------------------
API_TOKEN = "my_secret_token_123"

# ------------------- HTTP-сервер для обновления статуса -------------------
# UPDATE_SPOT_URL = "http://localhost/eazypark.kz/camera/update_spot.php"
UPDATE_SPOT_URL = "https://easypark.kz/camera/update_spot.php"

# ------------------- Файл для хранения зон -------------------
ZONES_FILE = "zones.json"

# ------------------- RTSP -------------------
# Основной URL-адрес для RTSP-потока камеры.
RTSP_URL = "rtsp://xkhu:ak4rax@192.168.100.34:554/cam/realmonitor?channel=1&subtype=0"
# Путь к модели YOLO (если будем использовать)
MODEL_PATH = "models/yolov10n.pt"

# ------------------- GUI / Headless -------------------
SHOW_WINDOW = False   # False = без окон (работа демоном)
