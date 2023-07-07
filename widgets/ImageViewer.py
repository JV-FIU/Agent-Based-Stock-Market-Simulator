from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget,  QLabel, QHBoxLayout, QVBoxLayout, QPushButton 
from PySide6 import QtCore

class ImageWidget(QWidget):
    def __init__(self, imageLocation):
        super().__init__()

        self.setWindowTitle("Liquidity Telemetry")

        imgLabel = QLabel()
        imgLabel.setPixmap(QPixmap(imageLocation).scaled(760, 950, QtCore.Qt.KeepAspectRatio)) #FIXME: Real image is HUGE, Must find a way to add zoom

        boxLayout = QVBoxLayout()
        boxLayout.addWidget(imgLabel)

        self.setLayout(boxLayout)


