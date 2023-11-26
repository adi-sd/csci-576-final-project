from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from moviepy.editor import VideoFileClip
import threading


class VideoPlayer(QWidget):
    def __init__(self, video_path, start_frame):
        super().__init__()
        self.video_path = video_path
        if not hasattr(self, "clip") or self.clip is None:
            self.clip = VideoFileClip(video_path)
        self.frame_number = start_frame
        self.initUI()
        self.updateFrame()

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
        self.pauseBtn.clicked.connect(self.pauseVideo)
        self.resetBtn.clicked.connect(self.resetVideo)

        self.pauseBtn.setEnabled(False)
        self.resetBtn.setEnabled(False)

        # Timer for frame updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.nextFrame)

    def showEvent(self, event):
        super().showEvent(event)
        self.updateFrame()

    def playVideo(self):
        if self.frame_number > 0:
            self.clip = self.clip.subclip(self.frame_number / self.clip.fps)

        # Start video playback
        self.timer.setInterval(int(1000 / self.clip.fps))
        self.timer.start()

        # Start audio playback
        self.clip.audio.preview()

        self.playBtn.setEnabled(False)
        self.pauseBtn.setEnabled(True)
        self.resetBtn.setEnabled(True)

    def pauseVideo(self):
        self.timer.stop()
        if hasattr(self, "clip") and self.clip is not None:
            self.clip.close()
            self.clip = None
        self.playBtn.setEnabled(True)
        self.pauseBtn.setEnabled(False)
        self.resetBtn.setEnabled(True)

    def resetVideo(self):
        self.frame_number = 0
        self.updateFrame()
        if hasattr(self, "clip") and self.clip is not None:
            self.clip.close()
            self.clip = None
        self.timer.stop()
        self.playBtn.setEnabled(True)
        self.pauseBtn.setEnabled(False)
        self.resetBtn.setEnabled(False)

    def nextFrame(self):
        if self.frame_number < self.clip.reader.nframes:
            self.frame_number += 1
            self.updateFrame()
        else:
            self.resetVideo()

    def updateFrame(self):
        frame = self.clip.get_frame(self.frame_number / self.clip.fps)
        height, width, _ = frame.shape
        print(f"Frame Height: {height}, Frame Width: {width}")
        qImage = QImage(
            frame,
            frame.shape[1],
            frame.shape[0],
            frame.strides[0],
            QImage.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(qImage)
        self.label.setPixmap(
            pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
        )
