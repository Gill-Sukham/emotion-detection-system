import sys
import cv2
import time
import random
import threading
import win32com.client

from collections import deque
from deepface import DeepFace

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyqtgraph as pg

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ---------------- UI CARDS ----------------
class NeonCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
        QFrame {
            background-color: rgba(10,10,20,0.9);
            border-radius: 20px;
            border: 2px solid #ff4da6;
        }
        """)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor("#ff4da6"))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

class PersonCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
        QFrame {
            background-color: rgba(20,20,30,0.85);
            border-radius: 12px;
            border: 2px solid #ff4da6;
        }
        """)
        layout = QHBoxLayout(self)
        self.label = QLabel("")
        self.label.setStyleSheet("color:#ff4da6; font-size:14px;")
        layout.addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)

# ---------------- MAIN APP ----------------
class EmotionUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Emotion AI 💖 Pro")
        self.resize(1100, 650)

        self.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #020617, stop:1 #0f172a);
        }
        QLabel { color:white; }
        """)

        # 🔊 FAST VOICE ENGINE (NO DELAY)
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.last_voice_time = time.time()
        self.voice_interval = 20
        self.latest_emotions = ["happy", "happy"]

        main = QWidget()
        self.setCentralWidget(main)
        main_layout = QHBoxLayout(main)

        # -------- SIDEBAR --------
        sidebar = QFrame()
        sidebar.setMaximumWidth(180)
        sidebar.setStyleSheet("""
        QFrame {
            background: rgba(15,15,25,0.95);
            border-right: 2px solid #ff4da6;
        }
        """)
        side_layout = QVBoxLayout(sidebar)

        self.start_btn = QPushButton("▶ Start")
        self.stop_btn = QPushButton("⏹ Stop")
        self.snap_btn = QPushButton("📸 Snapshot")
        self.reset_btn = QPushButton("🔄 Reset")

        for b in [self.start_btn, self.stop_btn, self.snap_btn, self.reset_btn]:
            b.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,77,166,0.2);
                border: 1px solid #ff4da6;
                border-radius: 8px;
                padding: 8px;
                color:white;
            }
            """)
            side_layout.addWidget(b)

        side_layout.addStretch()
        main_layout.addWidget(sidebar)

        # -------- CONTENT --------
        content = QVBoxLayout()

        header = QHBoxLayout()
        self.fps_label = QLabel("FPS: 0")
        self.time_label = QLabel()
        header.addWidget(self.fps_label)
        header.addStretch()
        header.addWidget(self.time_label)
        content.addLayout(header)

        top = QHBoxLayout()

        # LEFT BARS
        left = NeonCard()
        l_layout = QVBoxLayout(left)

        self.colors = {
            "happy": "#22c55e",
            "neutral": "#facc15",
            "sad": "#3b82f6",
            "surprise": "#a855f7",
            "angry": "#ef4444"
        }

        self.bars = {}
        for e in self.colors:
            lbl = QLabel(e.capitalize())
            bar = QProgressBar()
            bar.setMaximum(100)
            bar.setFixedHeight(10)
            bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255,255,255,0.08);
                border-radius:5px;
            }}
            QProgressBar::chunk {{
                background:{self.colors[e]};
            }}
            """)
            l_layout.addWidget(lbl)
            l_layout.addWidget(bar)
            self.bars[e] = bar

        # CAMERA
        center = NeonCard()
        c_layout = QVBoxLayout(center)

        self.camera = QLabel()
        self.camera.setFixedSize(640, 420)
        self.camera.setAlignment(Qt.AlignCenter)
        self.camera.setStyleSheet("background:black; border-radius:20px;")
        c_layout.addWidget(self.camera)

        # RIGHT PANEL
        right = NeonCard()
        r_layout = QVBoxLayout(right)

        self.person_cards = [PersonCard(), PersonCard()]
        for card in self.person_cards:
            r_layout.addWidget(card)

        top.addWidget(left, 1)
        top.addWidget(center, 3)
        top.addWidget(right, 1)

        content.addLayout(top)

        # GRAPH
        bottom = NeonCard()
        b_layout = QVBoxLayout(bottom)

        self.graph = pg.PlotWidget()
        self.graph.setBackground((0, 0, 0, 0))
        self.curve = self.graph.plot(pen=pg.mkPen('#ff4da6', width=3))
        b_layout.addWidget(self.graph)

        content.addWidget(bottom)
        main_layout.addLayout(content)

        # -------- DATA --------
        self.cap = cv2.VideoCapture(0)
        self.prev_time = time.time()
        self.history = deque(maxlen=30)
        self.frame_count = 0
        self.running = True

        # BUTTONS
        self.start_btn.clicked.connect(lambda: setattr(self, "running", True))
        self.stop_btn.clicked.connect(lambda: setattr(self, "running", False))
        self.snap_btn.clicked.connect(self.snapshot)
        self.reset_btn.clicked.connect(lambda: self.history.clear())

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(40)

        self.clock = QTimer()
        self.clock.timeout.connect(self.update_time)
        self.clock.start(1000)

    def update_time(self):
        self.time_label.setText(time.strftime("%d %b %Y | %I:%M:%S %p"))

    def snapshot(self):
        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite("snapshot.jpg", frame)

    # 🔊 ZERO DELAY SPEAK
    def speak(self, text):
        def run():
            try:
                self.speaker.Speak("", 3)   # STOP previous
                self.speaker.Speak(text, 1) # ASYNC
            except:
                pass
        threading.Thread(target=run, daemon=True).start()

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)

        now = time.time()
        fps = int(1 / (now - self.prev_time))
        self.prev_time = now
        self.fps_label.setText(f"FPS: {fps}")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=6,
            minSize=(100, 100)
        )

        faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)[:2]

        self.frame_count += 1

        # 🔥 VOICE EVERY 20 SEC (INSTANT)
        if time.time() - self.last_voice_time >= self.voice_interval:
            self.last_voice_time = time.time()

            for i in range(len(faces)):
                emo = self.latest_emotions[i]
                QTimer.singleShot(0, lambda p=i, e=emo: self.speak(f"Person {p+1} is {e}"))

        for i in range(2):
            if i < len(faces):
                x, y, w, h = faces[i]

                emotion = "happy"
                emotion_data = {}

                if self.frame_count % 6 == 0:
                    try:
                        face_img = frame[y:y+h, x:x+w]
                        res = DeepFace.analyze(face_img, actions=['emotion'], enforce_detection=False)
                        emotion = res[0]['dominant_emotion']
                        emotion_data = res[0]['emotion']
                    except:
                        pass

                self.latest_emotions[i] = emotion

                emoji = {
                    "happy": "😊", "sad": "😢", "angry": "😠",
                    "surprise": "😲", "neutral": "😐"
                }.get(emotion, "🙂")

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.putText(frame, f"P{i+1} {emoji}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

                self.person_cards[i].set_text(f"Person {i+1}   {emoji} {emotion}")
                self.person_cards[i].show()

                if emotion_data:
                    self.history.append(emotion_data.get('happy', 0))
                    self.curve.setData(list(self.history))

                    for e, v in emotion_data.items():
                        if e in self.bars:
                            self.bars[e].setValue(int(v))
            else:
                self.person_cards[i].hide()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)

        self.camera.setPixmap(QPixmap.fromImage(img).scaled(
            self.camera.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def closeEvent(self, e):
        self.cap.release()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EmotionUI()
    win.show()
    sys.exit(app.exec_())
