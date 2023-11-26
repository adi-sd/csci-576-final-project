import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap


class VideoPlayer(QWidget):
    def __init__(self, video_path, start_frame):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.nextFrameSlot)
        self.playing = False

    def initUI(self):
        self.setWindowTitle("Video Player")

        self.play_button = QPushButton("Play/Pause", self)
        self.play_button.clicked.connect(self.playPause)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.resetVideo)

        self.image_label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.play_button)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def playPause(self):
        if self.playing:
            self.timer.stop()
            self.playing = False
        else:
            self.timer.start(int(1000 / 30))  # assuming 30 fps video
            self.playing = True

    def resetVideo(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.playPause()

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        if not ret:
            self.resetVideo()
            return

        # Convert frame to format suitable for PyQt
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.image_label.setPixmap(pix)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer(
        "../../resources/video11.mp4", 0
    )  # Replace with your video path and start frame
    sys.exit(app.exec_())
