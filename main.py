import sys
from PyQt5.QtWidgets import QApplication
from modules.video_player.video_player import VideoPlayer


def main():
    app = QApplication(sys.argv)
    player = VideoPlayer("./resources/video11.mp4", "./resources/video11.wav", 100)
    player.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
