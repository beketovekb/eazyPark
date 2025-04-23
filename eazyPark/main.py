# eazyPark/main.py
import sys, time, cv2, numpy as np, os
from pathlib import Path
from eazyPark import config, detection
from eazyPark.zones   import (ZONES, load_zones, save_zones,
                              bbox_in_zone, add_zone, remove_zone)
from eazyPark.network import send_zone_status

# ───────────────────────────────────────────────────────────────
DISPLAY_W, DISPLAY_H = 960, 540          # используется только в GUI
RIGHT_PANE           = 320
AUTO_SEND_INTERVAL   = 60                # сек
# ───────────────────────────────────────────────────────────────

# ╔════════════════════════════════════════════════════════════╗
# ║                       HEADLESS МОД                       ║
# ╚════════════════════════════════════════════════════════════╝
def run_headless():
    from eazyPark.camera import CameraCapture

    load_zones()
    last_summary = 0
    cam = CameraCapture()
    if not cam.cap.isOpened():
        print("[ERR] Камера не открыта"); return

    print("[INFO] Headless-режим начат; Ctrl-C для остановки")
    try:
        while True:
            ok, frame = cam.get_frame()
            if not ok:
                time.sleep(1); continue

            detections = detection.detect_cars(frame)
            used = set()
            for det in detections:
                if any(bbox_in_zone(det["bbox"], z["points"])
                       for z in ZONES for _ in [used.add(ZONES.index(z))]):
                    pass   # used наполняется comprehension-ом

            # мгновенное отправление изменений
            for i,z in enumerate(ZONES):
                new_busy = i in used
                if z.get("busy") != new_busy:
                    z["busy"] = new_busy
                    send_zone_status(z["name"], new_busy,
                                     config.CAMERA_NAME,
                                     config.CAMERA_COUNTRY, config.CAMERA_REGION,
                                     config.CAMERA_CITY,    config.CAMERA_STREET,
                                     config.CAMERA_COORDS)

            # периодическая сводка
            if time.time() - last_summary > AUTO_SEND_INTERVAL:
                for z in ZONES:
                    send_zone_status(z["name"], z["busy"],
                                     config.CAMERA_NAME,
                                     config.CAMERA_COUNTRY, config.CAMERA_REGION,
                                     config.CAMERA_CITY,    config.CAMERA_STREET,
                                     config.CAMERA_COORDS)
                last_summary = time.time()

    except KeyboardInterrupt:
        print("\n[INFO] Остановлено пользователем")
    finally:
        cam.release()

# ╔════════════════════════════════════════════════════════════╗
# ║                         GUI-МОД                           ║
# ╚════════════════════════════════════════════════════════════╝
def run_gui():
    from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QListWidget,
                                 QPushButton, QVBoxLayout, QHBoxLayout,
                                 QListWidgetItem, QMessageBox)
    from PyQt5.QtGui  import QImage, QPixmap
    from PyQt5.QtCore import Qt
    from eazyPark.video_thread import VideoThread
    from eazyPark.ui           import NameDialog, SettingsDialog

    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("EazyPark Smart Vision")
            self.setFixedSize(DISPLAY_W + RIGHT_PANE, DISPLAY_H)

            self.video = QLabel("Video"); self.video.setAlignment(Qt.AlignCenter)
            self.video.setFixedSize(DISPLAY_W, DISPLAY_H)
            self.list  = QListWidget()
            self.btn_add = QPushButton("Новая зона")
            self.btn_set = QPushButton("⚙")

            side = QVBoxLayout(); side.addWidget(self.btn_set)
            side.addWidget(self.list,1); side.addWidget(self.btn_add)
            lay  = QHBoxLayout(self); lay.addWidget(self.video,1); lay.addLayout(side)

            self.btn_add.clicked.connect(self.new_zone)
            self.btn_set.clicked.connect(lambda: SettingsDialog(config,self).exec_())
            self.list.itemClicked.connect(self.del_zone)

            load_zones(); self.sync_list()
            self.drawing, self.tmp_pts, self.tmp_name = False, [], None
            self.last_summary = 0

            self.vth = VideoThread(); self.vth.frame_ready.connect(self.on_frame)
            self.vth.start()

        # ----------- кадр ------------
        def on_frame(self, frame):
            self.current = frame.copy()
            # рисуем зоны
            for z in ZONES:
                col = (0,0,255) if z.get("busy") else (0,255,0)
                cv2.polylines(frame,[np.array(z["points"]).reshape((-1,1,2))],True,col,2)
            # временные точки
            if self.drawing:
                self.video.mousePressEvent = self.click_video
                for i in range(len(self.tmp_pts)-1):
                    cv2.line(frame,self.tmp_pts[i],self.tmp_pts[i+1],(0,0,255),2)
                for p in self.tmp_pts:
                    cv2.circle(frame,p,5,(0,0,255),-1)

            # детекция
            used=set()
            for det in detection.detect_cars(frame):
                if any(bbox_in_zone(det["bbox"],z["points"])
                       for z in ZONES for _ in [used.add(ZONES.index(z))]):
                    pass
            for i,z in enumerate(ZONES):
                if z.get("busy")!= (i in used):
                    z["busy"]= i in used
                    send_zone_status(z["name"],z["busy"],
                                     config.CAMERA_NAME,
                                     config.CAMERA_COUNTRY,config.CAMERA_REGION,
                                     config.CAMERA_CITY,   config.CAMERA_STREET,
                                     config.CAMERA_COORDS)
            self.sync_list()

            if time.time()-self.last_summary> AUTO_SEND_INTERVAL:
                for z in ZONES:
                    send_zone_status(z["name"],z["busy"],
                                     config.CAMERA_NAME,
                                     config.CAMERA_COUNTRY,config.CAMERA_REGION,
                                     config.CAMERA_CITY,   config.CAMERA_STREET,
                                     config.CAMERA_COORDS)
                self.last_summary=time.time()

            rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            disp=cv2.resize(rgb,(DISPLAY_W,DISPLAY_H),interpolation=cv2.INTER_AREA)
            h,w,ch=disp.shape
            self.video.setPixmap(QPixmap.fromImage(
                QImage(disp.data,w,h,ch*w,QImage.Format_RGB888)))

        # ---------- клики ----------
        def click_video(self,e):
            if not self.drawing: return
            x = int(e.pos().x()*self.current.shape[1]/DISPLAY_W)
            y = int(e.pos().y()*self.current.shape[0]/DISPLAY_H)
            if e.button()==Qt.LeftButton:
                self.tmp_pts.append((x,y))
            elif e.button()==Qt.RightButton:
                if len(self.tmp_pts)<3:
                    QMessageBox.warning(self,"Мало точек","Нужно ≥3 точек"); return
                add_zone(self.tmp_name,self.tmp_pts.copy()); save_zones(); self.sync_list()
                self.drawing,self.tmp_pts=False,[]

        # ---------- список ----------
        def sync_list(self):
            self.list.clear()
            for z in ZONES:
                self.list.addItem(QListWidgetItem(
                    f"{z['name']:<12} | {'Занята' if z['busy'] else 'Свободна'}"))

        def new_zone(self):
            d=NameDialog(self)
            if d.exec_():
                self.drawing=True
                self.tmp_name=d.name or f"Zone{len(ZONES)+1}"
                self.tmp_pts.clear()
                QMessageBox.information(self,"Рисование",
                    "ЛКМ – точка, ПКМ – завершить")

        def del_zone(self,item):
            idx=self.list.row(item)
            if QMessageBox.question(self,"Удалить?",
               f"Удалить {ZONES[idx]['name']}?")==QMessageBox.Yes:
                remove_zone(idx); save_zones(); self.sync_list()

        def closeEvent(self,e):
            self.vth.stop(); e.accept()

    # ----- запуск GUI -----
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app=QApplication(sys.argv)
    Path("zones.json").touch(exist_ok=True)
    w=MainWindow(); w.show()
    sys.exit(app.exec_())

# ╔════════════════════════════════════════════════════════════╗
# ║                             MAIN                          ║
# ╚════════════════════════════════════════════════════════════╝
if __name__ == "__main__":
    if config.SHOW_WINDOW:
        run_gui()
    else:
        run_headless()
