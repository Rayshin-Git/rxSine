from ...core.json_themes import Themes
from ....qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QComboBox{{
border: {_border_size}px solid {_border_color};
background-color:{_bg_color}; 
color: {_text_color};
font: {_text_font};
}}
'''


# PY PUSH BUTTON
# ///////////////////////////////////////////////////////////////
class PyCombobox(QtWidgets.QComboBox):
    def __init__(
            self,
            parent=None,
            border_size=2,
            border_color="#343b48",
            text_color="#fff",
            text_font="9pt 'Segoe UI'",
    ):
        super(PyCombobox, self).__init__()
        themes = Themes()
        self.themes = themes.items
        self.setFixedHeight(24 * DPI_SCALE)
        # SET PARAMETRES
        if parent is not None:
            self.setParent(parent)
        self.border_size = border_size
        self.border_color = border_color
        self.text_color = text_color
        self.text_font = text_font

        # SET STYLESHEET
        custom_style = style.format(
            _border_size=2,
            _border_color=self.themes["app_color"]["dark_three"],
            _bg_color=self.themes["app_color"]["dark_one"],
            _text_color=self.text_color,
            _text_font=self.text_font,
        )

        self.setStyleSheet(custom_style)
