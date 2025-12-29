#This is a class which lets me click on the labels in the survey.
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSignal

class QClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)