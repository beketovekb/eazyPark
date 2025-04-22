# eazyPark/server.py

import requests
from .config import (
    API_TOKEN, CAMERA_NAME, CAMERA_COUNTRY, CAMERA_REGION,
    CAMERA_CITY, CAMERA_STREET, CAMERA_COORDS,
    UPDATE_SPOT_URL
)

def send_spot_update_json(zone_id, is_busy):
    data = {
        "token": API_TOKEN,
        "camera_name": CAMERA_NAME,
        "spot_id": zone_id,
        "country": CAMERA_COUNTRY,
        "region": CAMERA_REGION,
        "city": CAMERA_CITY,
        "street": CAMERA_STREET,
        "coords": CAMERA_COORDS,
        "is_busy": 1 if is_busy else 0
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(UPDATE_SPOT_URL, json=data, headers=headers, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            print(f"[ERROR] Server error: {result['error']}")
        else:
            print(f"[INFO] Spot {zone_id} updated: is_busy={is_busy}")
    except Exception as e:
        print(f"[ERROR] Failed to send spot update for {zone_id}: {e}")

def send_spot_delete_json(zone_id):
    data = {
        "token": API_TOKEN,
        "camera_name": CAMERA_NAME,
        "spot_id": zone_id,
        "action": "delete"
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(UPDATE_SPOT_URL, json=data, headers=headers, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            print(f"[ERROR] Server error: {result['error']}")
        else:
            print(f"[INFO] Spot {zone_id} deleted on server.")
    except Exception as e:
        print(f"[ERROR] Failed to delete spot {zone_id} on server: {e}")
