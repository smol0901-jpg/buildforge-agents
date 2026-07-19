from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QComboBox, QLineEdit, QMessageBox
)
from core.orchestrator import Orchestrator
from core.types import Mode
from core.event_bus import BUS
from llm.router import make_llm
from neural_core import KERNEL_NAME, KERNEL_VERSION, CONTACTS

class BuildWorker(QThread):
    done = Signal(object)
    def __init__(self, orch, project, mode, target):
        super().__init__()
        self.orch, self.project, self.mode, self.target = orch, project, mode, target
    def run(self):
        self.done.emit(self.orch.run(self.project, mode=self.mode, target=self.target))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"⚒️ {KERNEL_NAME} · {KERNEL_VERSION}")
        self.resize(980, 720)
        self.orch = Orchestrator()
        self.worker = None
        w = QWidget(); self.setCentralWidget(w)
        lay = QVBoxLayout(w)
        top = QHBoxLayout()
        self.proj = QLineEdit(); self.proj.setPlaceholderText("Папка проекта…")
        btn_browse = QPushButton("📁"); btn_browse.clicked.connect(self.browse)
        top.addWidget(self.proj, 1); top.addWidget(btn_browse); lay.addLayout(top)
        row = QHBoxLayout()
        self.mode = QComboBox(); self.mode.addItems(["autopilot", "manual", "neural"])
        self.llm = QComboBox(); self.llm.addItems(["none", "ollama", "gguf", "openai"])
        self.model = QLineEdit("qwen2.5:7b")
        self.target = QComboBox(); self.target.addItems(["exe+installer", "exe", "zip"])
        for lab, wid in [("Режим", self.mode), ("LLM", self.llm), ("Модель", self.model), ("Цель", self.target)]:
            row.addWidget(QLabel(lab)); row.addWidget(wid)
        lay.addLayout(row)
        btns = QHBoxLayout()
        self.btn_run = QPushButton("▶ Запуск"); self.btn_stop = QPushButton("⏹ Стоп"); self.btn_phone = QPushButton("📱 Phone")
        self.btn_run.clicked.connect(self.start_build)
        self.btn_stop.clicked.connect(lambda: self.orch.stop())
        self.btn_phone.clicked.connect(self.start_phone)
        btns.addWidget(self.btn_run); btns.addWidget(self.btn_stop); btns.addWidget(self.btn_phone); lay.addLayout(btns)
        self.status = QLabel(f"{KERNEL_NAME} готов · {CONTACTS.get('telegram')}"); lay.addWidget(self.status)
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#0d1117;color:#e6edf3;font-family:Consolas,monospace"); lay.addWidget(self.log, 1)
        chat_row = QHBoxLayout()
        self.chat = QLineEdit(); self.chat.setPlaceholderText("Команда / вопрос к NAP++…")
        btn_send = QPushButton("↵"); btn_send.clicked.connect(self.send_chat)
        chat_row.addWidget(self.chat, 1); chat_row.addWidget(btn_send); lay.addLayout(chat_row)
        BUS.on("log", self._on_log); BUS.on("status", self._on_status)
        self.setStyleSheet("QMainWindow,QWidget{background:#161b22;color:#e6edf3} QPushButton{background:#1f6feb;padding:8px;border-radius:6px} QLineEdit,QComboBox{background:#0d1117;padding:6px;border:1px solid #30363d;border-radius:6px}")

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Проект")
        if d: self.proj.setText(d)
    def _apply_llm(self):
        self.orch.set_llm(make_llm(self.llm.currentText(), model=self.model.text().strip()))
    def start_build(self):
        project = self.proj.text().strip()
        if not project or not Path(project).is_dir():
            QMessageBox.warning(self, "BuildForge", "Укажи папку проекта"); return
        self._apply_llm(); self.btn_run.setEnabled(False)
        self.worker = BuildWorker(self.orch, project, Mode(self.mode.currentText()), self.target.currentText())
        self.worker.done.connect(self._done); self.worker.start()
    def _done(self, res):
        self.btn_run.setEnabled(True)
        self.log.append(f"\n=== DONE ok={res.ok} stage={res.stage.value} ===")
        for a in res.artifacts: self.log.append(f"  • {a}")
        self.status.setText(res.message)
    def _on_log(self, data: dict):
        self.log.append(f"[{data.get('agent','')}] {data.get('message','')}")
    def _on_status(self, data: dict):
        self.status.setText(f"{data.get('stage')}: {data.get('message')} ({int((data.get('progress') or 0)*100)}%)")
    def send_chat(self):
        text = self.chat.text().strip()
        if not text: return
        self.chat.clear(); self._apply_llm()
        ans = self.orch.neural_chat(text, self.proj.text().strip() or None)
        self.log.append(f"\nYOU: {text}\nNAP++: {ans}")
    def start_phone(self):
        import threading
        from server.phone_api import run_phone_server
        threading.Thread(target=lambda: run_phone_server(self.orch, port=8787), daemon=True).start()
        self.log.append("Phone: http://0.0.0.0:8787")

def run_ui():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())
