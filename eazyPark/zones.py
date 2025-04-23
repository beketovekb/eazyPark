# eazyPark/zones.py
import json, os
from shapely.geometry import Point, Polygon

#   новый формат: [{ "name": str, "points": [[x,y],…], "busy": false }, …]
ZONES = []

# ──────────────────────────────────────────────────────────────────────────────
def add_zone(name: str, points):
    ZONES.append({"name": name, "points": points, "busy": False})

def remove_zone(idx: int):
    if 0 <= idx < len(ZONES):
        ZONES.pop(idx)

# ──────────────────────────────────────────────────────────────────────────────
def point_in_zone(x, y, zone_pts):
    return Polygon(zone_pts).contains(Point(x, y))

def bbox_in_zone(bbox, zone_pts):
    x1, y1, x2, y2 = bbox
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    return point_in_zone(cx, cy, zone_pts)

# ──────────────────────────────────────────────────────────────────────────────
def save_zones(path="zones.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ZONES, f, ensure_ascii=False, indent=2)

def load_zones(path="zones.json"):
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("[WARN] zones.json пустой или повреждён → игнорирую")
        data = []

    ZONES.clear()
    for i,item in enumerate(data):
        if isinstance(item, list):                 # старый формат
            ZONES.append({"name": f"Zone{i+1}",
                          "points": item, "busy": False})
        else:
            ZONES.append(item)

