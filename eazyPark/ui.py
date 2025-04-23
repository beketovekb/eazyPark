# eazyPark/ui.py
import re, inspect, textwrap
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QGridLayout, QMessageBox)

# ──────────────────────────────────────────────────────────────────────────────
class NameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая зона")
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Введите название:"))
        self.edit = QLineEdit()
        v.addWidget(self.edit)
        btn = QPushButton("Далее"); v.addWidget(btn)
        btn.clicked.connect(self.accept)

    @property
    def name(self):
        return self.edit.text().strip() or None

# ──────────────────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    FIELDS = ["CAMERA_COUNTRY","CAMERA_REGION","CAMERA_CITY","CAMERA_STREET",
              "CAMERA_COORDS","CAMERA_NAME","UPDATE_SPOT_URL","RTSP_URL"]

    def __init__(self, cfg_module, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.mod = cfg_module
        g = QGridLayout(self)
        self.edits = {}
        for i,k in enumerate(self.FIELDS):
            g.addWidget(QLabel(k.replace("_"," ").title()+":"), i, 0)
            e = QLineEdit(str(getattr(cfg_module, k))); g.addWidget(e, i,1)
            self.edits[k] = e
        ok = QPushButton("Сохранить"); g.addWidget(ok, len(self.FIELDS), 0,1,2)
        ok.clicked.connect(self.save)

    # ───────────────────────────────────────
    def save(self):
        path = Path(inspect.getfile(self.mod))
        src  = path.read_text(encoding="utf-8")
        for k,e in self.edits.items():
            val = e.text().replace("\\","\\\\").replace('"','\\"')
            src = re.sub(rf'{k}\s*=\s*".*?"', f'{k} = "{val}"', src, 1)
        path.write_text(src, encoding="utf-8")
        QMessageBox.information(self,"OK","Изменения сохранены.\nПерезапустите программу.")
        self.accept()
