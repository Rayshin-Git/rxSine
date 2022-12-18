from ...core.json_themes import Themes
from ....qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
QListWidget{{
border: {_border_size}px solid {_border_color};
background : {_bg_color};
color: {_text_color};
font: {_text_font};
}}
 QListView::item:selected
{{
border : {_border_size}px solid {_border_color};
background : {_bg_color_2};
}}

/* /////////////////////////////////////////////////////////////////////////////////////////////////
ScrollBars */
QScrollBar:horizontal {{
    border: none;
    background: {_scroll_bar_bg_color};
    height: 12px;
    margin: 0px 0px 0 0px;
	border-radius: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {_context_color};
    min-width: 25px;
	border-radius: 4px
}}
QScrollBar::add-line:horizontal {{
    border: none;
    background: {_scroll_bar_btn_color};
    width: 20px;
	border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}}
QScrollBar::sub-line:horizontal {{
    border: none;
    background: {_scroll_bar_btn_color};
    width: 20px;
	border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}}
QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
{{
     background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{{
     background: none;
}}
QScrollBar:vertical {{
	border: none;
    background: {_scroll_bar_bg_color};
    width: 8px;
    margin: 21px 0 21px 0;
	border-radius: 0px;
}}
QScrollBar::handle:vertical {{	
	background: {_context_color};
    min-height: 25px;
	border-radius: 4px
}}
QScrollBar::add-line:vertical {{
     border: none;
    background: {_scroll_bar_btn_color};
     height: 20px;
	border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
     subcontrol-position: bottom;
     subcontrol-origin: margin;
}}
QScrollBar::sub-line:vertical {{
	border: none;
    background: {_scroll_bar_btn_color};
     height: 20px;
	border-top-left-radius: 4px;
    border-top-right-radius: 4px;
     subcontrol-position: top;
     subcontrol-origin: margin;
}}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
     background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
     background: none;
}}
'''
scroll_bar_btn_color = "#3333"
context_color = "#00ABE8"


# PY PUSH BUTTON
# ///////////////////////////////////////////////////////////////
class PyListWidget(QtWidgets.QListWidget):
    def __init__(
            self,
            parent=None,
    ):
        super(PyListWidget, self).__init__()
        themes = Themes()
        self.themes = themes.items
        # SET PARAMETRES
        if parent is not None:
            self.setParent(parent)

        # SET STYLESHEET
        custom_style = style.format(
            _border_size=self.themes["app_color"]["text_foreground"],
            _border_color=self.themes["app_color"]["text_foreground"],
            _radius=8,
            _bg_color=self.themes["app_color"]["dark_three"],
            _bg_color_2=self.themes["app_color"]["text_description"],
            _scroll_bar_bg_color=self.themes["app_color"]["bg_one"],
            _scroll_bar_btn_color=scroll_bar_btn_color,
            _context_color="#568af2",
            _text_color="#fff",
            _text_font="9pt 'Segoe UI'",
        )
        self.setStyleSheet(custom_style)
