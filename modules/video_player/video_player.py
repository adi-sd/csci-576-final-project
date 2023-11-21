import cv2
import pygame
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class VideoPlayer(QWidget):
    def __init__(self, video_path, start_time):
        super().__init__()
        self.is_video_paused = False
        self.video_path = video_path
        self.start_time = start_time
        self.initUI()

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load the audio from the video file
        try:
            pygame.mixer.music.load(self.video_path)
        except Exception as e:
            print(f"Error loading audio: {e}")

    def initUI(self):
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 800)

        # Video display
        self.label = QLabel(self)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.label)
        self.setLayout(self.vbox)

        # Buttons
        self.bbox = QHBoxLayout()
        self.playBtn = QPushButton("Play", self)
        self.pauseBtn = QPushButton("Pause", self)
        self.resetBtn = QPushButton("Reset", self)

        self.bbox.addWidget(self.playBtn)
        self.bbox.addWidget(self.pauseBtn)
        self.bbox.addWidget(self.resetBtn)

        self.vbox.addLayout(self.bbox)

        self.playBtn.clicked.connect(self.playVideo)
        self.pauseBtn.clicked.connect(self.togglePause)
        self.resetBtn.clicked.connect(self.resetVideo)

        self.pauseBtn.setEnabled(False)
        self.resetBtn.setEnabled(False)

        # Timer for video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.nextFrame)
        self.cap = None

    def playVideo(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.video_path)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.cap.set(cv2.CAP_PROP_POS_MSEC, self.start_time * 1000)
            self.timer.setInterval(int(1000 / fps))

        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(start=self.start_time)

        self.pauseBtn.setEnabled(True)
        self.resetBtn.setEnabled(True)
        self.timer.start()

    def togglePause(self):
        if self.is_video_paused:
            self.resumeVideo()
        else:
            self.pauseVideo()

    def pauseVideo(self):
        self.timer.stop()
        pygame.mixer.music.pause()
        self.pauseBtn.setText("Resume")
        self.is_video_paused = True

    def resumeVideo(self):
        self.timer.start()
        pygame.mixer.music.unpause()
        self.pauseBtn.setText("Pause")
        self.is_video_paused = False

    def resetVideo(self):
        self.timer.stop()
        self.cap.set(cv2.CAP_PROP_POS_MSEC, 0)
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=0)
        self.nextFrame()

    def nextFrame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(
                rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            p = convert_to_Qt_format.scaled(800, 800, Qt.KeepAspectRatio)
            self.label.setPixmap(QPixmap.fromImage(p))
