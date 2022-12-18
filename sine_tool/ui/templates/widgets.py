# coding=utf-8
from PySide2 import QtWidgets, QtCore

from ...ui.widgets.py_slider import PySlider


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)


class IntSliderGroup(QtWidgets.QHBoxLayout):
    valueChange = QtCore.Signal(int)

    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.slider = PySlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.spin = QtWidgets.QSpinBox()
        self.addWidget(self.spin)
        self.addWidget(self.slider)
        self.set_range(1, 10)
        self.spin.valueChanged.connect(self.convert_slider)
        self.slider.valueChanged.connect(self.convert_spin)

    def convert_spin(self, value):
        self.spin.setValue(int(value))
        self.valueChange.emit(self.spin.value())

    def convert_slider(self, value):
        self.slider.setValue(int(value))

    def set_range(self, min_value, max_value):
        self.spin.setRange(min_value, max_value)
        self.slider.setRange(min_value, max_value)

    def value(self):
        return self.spin.value()

    def set_value(self, value):
        self.spin.setValue(value)


class FloatSliderGroup(QtWidgets.QHBoxLayout):
    valueChange = QtCore.Signal(float)

    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.slider = PySlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.spin = QtWidgets.QDoubleSpinBox()
        self.addWidget(self.spin)
        self.addWidget(self.slider)
        self.set_range(0.01, 1)
        self.spin.valueChanged.connect(self.convert_slider)
        self.slider.valueChanged.connect(self.convert_spin)
        self.spin.setSingleStep(0.01)
        self.spin.setDecimals(3)

    def convert_spin(self, value):
        self.spin.setValue(value / 1000.0)
        self.valueChange.emit(self.spin.value())

    def convert_slider(self, value):
        self.slider.setValue(int(round(1000 * value)))

    def set_range(self, min_value, max_value):
        self.spin.setRange(min_value, max_value)
        self.slider.setRange(min_value * 1000, max_value * 1000)

    def value(self):
        return self.spin.value()

    def set_value(self, value):
        self.spin.setValue(value)


class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

# class CustomColorButton(QtWidgets.QWidget):
#     color_changed = QtCore.Signal(QtGui.QColor)
#
#     def __init__(self, color=QtCore.Qt.white, parent=None):
#         super(CustomColorButton, self).__init__(parent)
#
#         self.color = None
#         self.setObjectName("CustomColorButton")
#
#         self.create_control()
#
#         # self.set_size(900*DPI_SCALE, 20*DPI_SCALE)
#         self.set_color(color)
#
#     def create_control(self):
#         # Create the colorSliderGrp
#         window = cmds.window()
#         color_slider_name = cmds.colorSliderGrp()
#
#         # Find the colorSliderGrp widget
#         self._color_slider_obj = omui.MQtUtil.findControl(color_slider_name)
#         if self._color_slider_obj:
#             obj = long(self._color_slider_obj) if PY2 else int(self._color_slider_obj)  # noqa
#             self._color_slider_widget = wrapInstance(obj, QtWidgets.QWidget)
#
#             # Reparent the colorSliderGrp widget to this widget
#             main_layout = QtWidgets.QVBoxLayout(self)
#             main_layout.setObjectName("main_layout")
#             main_layout.setContentsMargins(0, 0, 0, 0)
#             main_layout.addWidget(self._color_slider_widget)
#
#             # Identify/store the colorSliderGrp’s child widgets (and hide if necessary)
#             # children = self._color_slider_widget.children()
#             # for child in children:
#             #     print(child)
#             #     print(child.objectName())
#             # print("---")
#
#             self._slider_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "slider")
#             if self._slider_widget:
#                 self._slider_widget.hide()
#
#             self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "port")
#
#             cmds.colorSliderGrp(self.get_full_name(), e=True, changeCommand=partial(self.on_color_changed))
#
#         cmds.deleteUI(window, window=True)
#
#     def get_full_name(self):
#         obj = long(self._color_slider_obj) if PY2 else int(self._color_slider_obj)  # noqa
#         return omui.MQtUtil.fullName(obj)
#
#     def set_size(self, width, height):
#         self._color_slider_widget.setFixedWidth(width)
#         self._color_widget.setFixedHeight(height)
#
#     def set_color(self, color):
#         color = QtGui.QColor(color)
#         self.color = color
#
#         cmds.colorSliderGrp(self.get_full_name(), e=True, rgbValue=(color.redF(), color.greenF(), color.blueF()))
#         self.on_color_changed()
#
#     def get_color(self):
#         # color = cmds.colorSliderGrp(self._color_slider_widget.objectName(), q=True, rgbValue=True)
#         color = cmds.colorSliderGrp(self.get_full_name(), q=True, rgbValue=True)
#
#         color = QtGui.QColor(color[0] * 255, color[1] * 255, color[2] * 255)
#         return color
#
#     def on_color_changed(self, *args):
#         self.color_changed.emit(self.get_color())
