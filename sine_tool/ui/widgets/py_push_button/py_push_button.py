from ...core.json_themes import Themes
from ....utils import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QPushButton {{
    border: none;
    padding-left: 10px;
    padding-right: 5px;
    color: {_color};
	border-radius: {_radius};	
	background-color: {_bg_color};
}}
QPushButton:hover {{
	background-color: {_bg_color_hover};
}}
QPushButton:pressed {{	
	background-color: {_bg_color_pressed};
}}
'''


# PY PUSH BUTTON
# ///////////////////////////////////////////////////////////////
class PyPushButton(QtWidgets.QPushButton):
    def __init__(
            self,
            text,
            parent=None,
    ):
        super(PyPushButton, self).__init__()
        themes = Themes()
        self.themes = themes.items
        self.setFixedHeight(24 * DPI_SCALE)
        # SET PARAMETRES
        self.setText(text)
        if parent is not None:
            self.setParent(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        # SET STYLESHEET
        custom_style = style.format(
            _color=self.themes["app_color"]["text_foreground"],
            _radius=8,
            _bg_color=self.themes["app_color"]["dark_one"],
            _bg_color_hover=self.themes["app_color"]["dark_three"],
            _bg_color_pressed=self.themes["app_color"]["dark_four"]
        )
        self.setStyleSheet(custom_style)
