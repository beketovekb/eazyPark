# eazyPark/network.py

import requests
from eazyPark.config import API_TOKEN, UPDATE_SPOT_URL

def send_zone_status(spot_id, is_busy, camera_name, country, region, city, street, coords):
    try:
        data = {
            "token": "my_secret_token_123",
            "camera_name": camera_name,
            "spot_id": spot_id,
            "is_busy": "1" if is_busy else "0",
            "country": country,
            "region": region,
            "city": city,
            "street": street,
            "coords": coords
        }
        response = requests.post(UPDATE_SPOT_URL, json=data, timeout=3)
        if response.status_code != 200:
            print(f"[ERROR] Не удалось отправить статус для {spot_id}: {response.text}")
    except Exception as e:
        print(f"[EXCEPTION] Ошибка при отправке статуса: {e}")
