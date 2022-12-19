from sine_tool.utils import *


# CUSTOM LEFT MENU
# ///////////////////////////////////////////////////////////////
class PyDiv(QtWidgets.QWidget):
    def __init__(self, color):
        super(PyDiv, self).__init__()

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.frame_line = QtWidgets.QFrame()
        self.frame_line.setStyleSheet("background: {};".format(color))
        self.frame_line.setMaximumWidth(1)
        self.frame_line.setMinimumWidth(1)
        self.layout.addWidget(self.frame_line)
        self.setMaximumWidth(20)
        self.setMinimumWidth(20)
