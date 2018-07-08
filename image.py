from os.path import abspath
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

app = QApplication(sys.argv)
w = QWidget()
w.setWindowTitle("Title!!!")

label = QLabel(w)
pixmap = QPixmap(abspath("rose-picture.png"))
label.setPixmap(pixmap)
# w.resize(pixmap.width(),pixmap.height())

w.show()
app.exec_()

