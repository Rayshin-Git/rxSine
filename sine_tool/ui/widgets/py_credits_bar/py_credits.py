from ....utils import *


# PY CREDITS BAR AND VERSION
# ///////////////////////////////////////////////////////////////
class PyCredits(QtWidgets.QWidget):
    def __init__(
            self,
            copyright,
            version,
            bg_two,
            font_family,
            text_size,
            text_description_color,
            radius=8,
            padding=10
    ):
        super(PyCredits, self).__init__()

        # PROPERTIES
        self._copyright = copyright
        self._version = version
        self._bg_two = bg_two
        self._font_family = font_family
        self._text_size = text_size
        self._text_description_color = text_description_color
        self._radius = radius
        self._padding = padding

        # SETUP UI
        self.setup_ui()

    def setup_ui(self):
        # ADD LAYOUT
        self.widget_layout = QtWidgets.QHBoxLayout(self)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)

        # BG STYLE
        style = """
        #bg_frame {{
            border-radius: {_radius}px;
            background-color: {_bg_two};
        }}
        .QLabel {{
            font: {_text_size}pt "{_font_family}";
            color: {_text_description_color};
            padding-left: {_padding}px;
            padding-right: {_padding}px;
        }}
        """.format(
            _radius=self._radius,
            _bg_two=self._bg_two,
            _text_size=self._text_size,
            _font_family=self._font_family,
            _text_description_color=self._text_description_color,
            _padding=self._padding
        )

        # BG FRAME
        self.bg_frame = QtWidgets.QFrame()
        self.bg_frame.setObjectName("bg_frame")
        self.bg_frame.setStyleSheet(style)

        # ADD TO LAYOUT
        self.widget_layout.addWidget(self.bg_frame)

        # ADD BG LAYOUT
        self.bg_layout = QtWidgets.QHBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(0, 0, 0, 0)

        # ADD COPYRIGHT TEXT
        self.copyright_label = QtWidgets.QLabel(self._copyright)
        self.copyright_label.setAlignment(QtCore.Qt.AlignVCenter)

        # ADD VERSION TEXT
        self.version_label = QtWidgets.QLabel(self._version)
        self.version_label.setAlignment(QtCore.Qt.AlignVCenter)

        # SEPARATOR
        self.separator = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # ADD TO LAYOUT
        self.bg_layout.addWidget(self.copyright_label)
        self.bg_layout.addSpacerItem(self.separator)
        self.bg_layout.addWidget(self.version_label)
