from ..core.json_settings import Settings
from ..core.json_themes import Themes
from ..widgets.py_credits_bar import PyCredits
from ..widgets.py_grips import PyGrips
from ..widgets.py_title_bar import PyTitleBar
from ...utils import *

app = maya_main_window()


class SubWindow(QtWidgets.QDialog, object):
    bg_style = """
    QDialog{{background:{_bg_color};
    border-radius: {_border_radius};
    border: {_border_size}px solid {_border_color};
    }}
    {{color: {_text_color};
    font: {_text_font};}}
    """

    def __init__(self,
                 parent=maya_main_window(),
                 bg_color="#2c313c",
                 text_color="#fff",
                 text_font="9pt 'Segoe UI'",
                 border_radius=10,
                 border_size=2,
                 border_color="#343b48",
                 enable_shadow=True
                 ):
        super(SubWindow, self).__init__(parent)

        # parameters >>>>>>>>>>>>>>>>
        self.window = None
        self.themes = None
        self.settings = None
        self.titleBar = None
        self.pressing = None
        self.bottom_right_grip = None
        self.bottom_left_grip = None
        self.top_right_grip = None
        self.top_left_grip = None
        self.bottom_grip = None
        self.top_grip = None
        self.right_grip = None
        self.left_grip = None
        self.hide_grips = None

        self.bg_color = bg_color
        self.text_color = text_color
        self.text_font = text_font
        self.border_radius = border_radius
        self.border_size = border_size
        self.border_color = border_color
        self.enable_shadow = enable_shadow
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<

        self.setup_main_layout()

    def setup_main_layout(self):
        parent = self.parent()
        if not parent.objectName():
            parent.setObjectName("MainWindow")

        # LOAD SETTINGS
        # ///////////////////////////////////////////////////////////////
        settings = Settings()
        self.settings = settings.items

        # LOAD THEME COLOR
        # ///////////////////////////////////////////////////////////////
        themes = Themes()
        self.themes = themes.items

        # SET INITIAL PARAMETERS

        self.layout = QtWidgets.QVBoxLayout(self)
        self.resize(self.settings["startup_size"][0], self.settings["startup_size"][1])
        self.setMinimumSize(self.settings["minimum_size"][0], self.settings["minimum_size"][1])
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._setup_titlebar()
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(10, 0, 10, 10)
        self.layout.addLayout(self.content_layout)
        # self.layout.addWidget(QtWidgets.QLabel())
        # self.layout.addStretch(-1)
        self.set_stylesheet()

    def setup_content(self, layout):
        if layout:
            self.layout.addLayout(layout)

    def set_stylesheet(
            self,
            bg_color=None,
            border_radius=None,
            border_size=None,
            border_color=None,
            text_color=None,
            text_font=None
    ):
        # CHECK BG COLOR
        if bg_color != None:
            internal_bg_color = bg_color
        else:
            internal_bg_color = self.bg_color

        # CHECK BORDER RADIUS
        if border_radius != None:
            internal_border_radius = border_radius
        else:
            internal_border_radius = self.border_radius

        # CHECK BORDER SIZE
        if border_size != None:
            internal_border_size = border_size
        else:
            internal_border_size = self.border_size

        # CHECK BORDER COLOR
        if text_color != None:
            internal_text_color = text_color
        else:
            internal_text_color = self.text_color

        # CHECK TEXT COLOR
        if border_color != None:
            internal_border_color = border_color
        else:
            internal_border_color = self.border_color

        # CHECK TEXT COLOR
        if text_font != None:
            internal_text_font = text_font
        else:
            internal_text_font = self.text_font

        self.setStyleSheet(self.bg_style.format(
            _bg_color=internal_bg_color,
            _border_radius=internal_border_radius,
            _border_size=internal_border_size,
            _border_color=internal_border_color,
            _text_color=internal_text_color,
            _text_font=internal_text_font,
        ))
        if self.settings["custom_title_bar"]:
            if self.enable_shadow:
                self.shadow = QtWidgets.QGraphicsDropShadowEffect()
                self.shadow.setBlurRadius(20)
                self.shadow.setXOffset(0)
                self.shadow.setYOffset(0)
                self.shadow.setColor(QtGui.QColor(0, 0, 0, 160))
                self.setGraphicsEffect(self.shadow)

    def _setup_titlebar(self):
        if PY2:
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.titleBar = PyTitleBar(
            # self.window,
            self,
            app,
            logo_width=100 * DPI_SCALE,
            logo_image="sine_logo.svg",
            bg_color=self.themes["app_color"]["bg_two"],
            div_color=self.themes["app_color"]["bg_three"],
            btn_bg_color=self.themes["app_color"]["bg_two"],
            btn_bg_color_hover=self.themes["app_color"]["bg_three"],
            btn_bg_color_pressed=self.themes["app_color"]["bg_one"],
            icon_color=self.themes["app_color"]["icon_color"],
            icon_color_hover=self.themes["app_color"]["icon_hover"],
            icon_color_pressed=self.themes["app_color"]["icon_pressed"],
            icon_color_active=self.themes["app_color"]["icon_active"],
            context_color=self.themes["app_color"]["context_color"],
            dark_one=self.themes["app_color"]["dark_one"],
            text_foreground=self.themes["app_color"]["text_foreground"],
            radius=8,
            font_family=self.settings["font"]["family"],
            title_size=self.settings["font"]["title_size"],
            is_custom_title_bar=self.settings["custom_title_bar"],
            default_btns=(0, 0, 1),
        )
        self.titleBar.set_title("Sine Tool")
        self.setWindowTitle("Sine Tool")
        self.layout.addWidget(self.titleBar)

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.FramelessWindowHint
                            )

    # def setup_grip(self):
    #     # advanced grip sample
    #     self.hide_grips = True
    #     self.left_grip = PyGrips(self, "left", self.hide_grips)
    #     self.right_grip = PyGrips(self, "right", self.hide_grips)
    #     self.top_grip = PyGrips(self, "top", self.hide_grips)
    #     self.bottom_grip = PyGrips(self, "bottom", self.hide_grips)
    #     self.top_left_grip = PyGrips(self, "top_left", self.hide_grips)
    #     self.top_right_grip = PyGrips(self, "top_right", self.hide_grips)
    #     self.bottom_left_grip = PyGrips(self, "bottom_left", self.hide_grips)
    #     self.bottom_right_grip = PyGrips(self, "bottom_right", self.hide_grips)
    #
    #     self.pressing = False
    #
    # def resize_grips(self):
    #     # if self.settings["custom_title_bar"]:
    #     self.left_grip.setGeometry(0, 10, 50, self.height())
    #     self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
    #     self.top_grip.setGeometry(5, 0, self.width() - 10, 10)
    #     self.bottom_grip.setGeometry(0, self.height() - 10, self.width() - 10, 10)
    #     self.top_right_grip.setGeometry(self.width() - 15, 0, 15, 15)
    #     self.top_left_grip.setGeometry(0, 0, 15, 15)
    #     self.bottom_left_grip.setGeometry(0, self.height() - 15, 15, 15)
    #     self.bottom_right_grip.setGeometry(self.width() - 15, self.height() - 15, 15, 15)

    def resizeEvent(self, event):
        if self.border_radius:
            path = QtGui.QPainterPath()
            # self.resize(440,220)
            path.addRoundedRect(QtCore.QRectF(self.rect()), self.border_radius, self.border_radius)
            mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
            self.setMask(mask)
        # self.resize_grips()

    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):

        if event.buttons() == QtCore.Qt.LeftButton:
            # self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()


class MainWindow(SubWindow, object):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setup_grip_custom()

    def _setup_titlebar(self):
        if PY2:
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.titleBar = PyTitleBar(
            self,
            app,
            logo_width=100 * DPI_SCALE,
            logo_image="sine_logo.svg",
            bg_color=self.themes["app_color"]["bg_two"],
            div_color=self.themes["app_color"]["bg_three"],
            btn_bg_color=self.themes["app_color"]["bg_two"],
            btn_bg_color_hover=self.themes["app_color"]["bg_three"],
            btn_bg_color_pressed=self.themes["app_color"]["bg_one"],
            icon_color=self.themes["app_color"]["icon_color"],
            icon_color_hover=self.themes["app_color"]["icon_hover"],
            icon_color_pressed=self.themes["app_color"]["icon_pressed"],
            icon_color_active=self.themes["app_color"]["icon_active"],
            context_color=self.themes["app_color"]["context_color"],
            dark_one=self.themes["app_color"]["dark_one"],
            text_foreground=self.themes["app_color"]["text_foreground"],
            radius=8,
            font_family=self.settings["font"]["family"],
            title_size=self.settings["font"]["title_size"],
            is_custom_title_bar=self.settings["custom_title_bar"],
            default_btns=(1, 1, 1),
        )
        self.titleBar.set_title("Sine Tool")
        self.setWindowTitle("Sine Tool")
        self.layout.addWidget(self.titleBar)

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.FramelessWindowHint
                            )

    def setup_grip_custom(self):
        # advanced grip sample
        self.hide_grips = True
        self.left_grip = PyGrips(self, "left", self.hide_grips)
        self.right_grip = PyGrips(self, "right", self.hide_grips)
        self.top_grip = PyGrips(self, "top", self.hide_grips)
        self.bottom_grip = PyGrips(self, "bottom", self.hide_grips)
        self.top_left_grip = PyGrips(self, "top_left", self.hide_grips)
        self.top_right_grip = PyGrips(self, "top_right", self.hide_grips)
        self.bottom_left_grip = PyGrips(self, "bottom_left", self.hide_grips)
        self.bottom_right_grip = PyGrips(self, "bottom_right", self.hide_grips)

        self.pressing = False

    def resize_grips(self):
        # if self.settings["custom_title_bar"]:
        self.left_grip.setGeometry(0, 10, 50, self.height())
        self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
        self.top_grip.setGeometry(5, 0, self.width() - 10, 10)
        self.bottom_grip.setGeometry(0, self.height() - 10, self.width() - 10, 10)
        self.top_right_grip.setGeometry(self.width() - 15, 0, 15, 15)
        self.top_left_grip.setGeometry(0, 0, 15, 15)
        self.bottom_left_grip.setGeometry(0, self.height() - 15, 15, 15)
        self.bottom_right_grip.setGeometry(self.width() - 15, self.height() - 15, 15, 15)

    def resizeEvent(self, event):
        if self.border_radius:
            path = QtGui.QPainterPath()
            # self.resize(440,220)
            path.addRoundedRect(QtCore.QRectF(self.rect()), self.border_radius, self.border_radius)
            mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
            self.setMask(mask)
        self.resize_grips()
