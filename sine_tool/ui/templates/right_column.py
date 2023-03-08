# coding=utf-8
from ..core.functions import Functions
from ..core.json_settings import Settings
from ..core.json_themes import Themes
from ..widgets.py_icon_button import PyIconButton
from ..widgets.py_line_edit import PyLineEdit
from ..widgets.py_list_widget import PyListWidget
from ...utils import *


class RightColumn(QtWidgets.QWidget):
    """
    All non-UI related methods and connections are written in the mainUI
    """

    def __init__(self, parent=None, app_parent=None):
        super(RightColumn, self).__init__()
        # SET PARAMETRES
        if parent is not None:
            self.setParent(parent)
        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        settings = Settings()
        self.settings = settings.items
        font = QtGui.QFont()
        font.setPointSize(self.settings["font"]["text_size"])
        font.setBold(True)
        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        # if not self.objectName():
        #     self.setObjectName(u"RightColumn")
        self.resize(240*DPI_SCALE, 600*DPI_SCALE)
        _L = ["EN", "JP"].index(self.settings["language"])
        # LAYOUT
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.top_layout = QtWidgets.QHBoxLayout()

        # WIDGETS
        text = ["Set Path to Import/Export Preset", "プレセットのパスを設定する"]
        self.top_label = QtWidgets.QLabel(text[_L])
        self.top_label.setAlignment(QtCore.Qt.AlignCenter)
        self.top_label.setFont(font)
        self.top_label.setMargin(4)
        self.path_le = PyLineEdit()
        self.path_le.setFocusPolicy(QtCore.Qt.ClickFocus)
        text = ["Select Path", "パスを設定"]
        self.setPath_btn = PyIconButton(icon_path=Functions.set_svg_icon("icon_folder_open.svg"),
                                        parent=self.parent(),
                                        app_parent=self.parent(),
                                        tooltip_text=text[_L],
                                        bg_color=self.themes["app_color"]["bg_three"],
                                        bg_color_hover="#1e2229",
                                        bg_color_pressed=self.themes["app_color"]["dark_one"],
                                        width=25,
                                        height=25,
                                        offsetPos=[0, -20]
                                        )
        text = ["Export Preset", "プリセット出力"]
        self.export_btn = PyIconButton(icon_path=Functions.set_svg_icon("icon_save.svg"),
                                       parent=self.parent(),
                                       app_parent=self.parent(),
                                       tooltip_text=text[_L],
                                       bg_color=self.themes["app_color"]["bg_three"],
                                       bg_color_hover="#1e2229",
                                       bg_color_pressed=self.themes["app_color"]["dark_one"],
                                       width=25,
                                       height=25,
                                       offsetPos=[-25, -20]
                                       )
        self.file_lst = PyListWidget()

        # SETUP
        self.top_layout.addWidget(self.path_le)
        self.top_layout.addWidget(self.setPath_btn)
        self.top_layout.addWidget(self.export_btn)

        self.main_layout.addWidget(self.top_label)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.file_lst)
