#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import json

from .widgets.py_credits_bar import PyCredits
from ..six import ensure_text
from functools import partial

from maya import cmds

import pymel.core as pm

from .core.functions import Functions
from ..ui.templates.main_window import MainWindow, SubWindow
from ..ui.templates.widgets import IntSliderGroup, FloatSliderGroup, FlowLayout
from ..ui.widgets.py_combobox import PyCombobox
from ..ui.widgets.py_list_widget import PyListWidget
from ..ui.widgets.py_push_button import PyPushButton
from .widgets.py_icon_button import PyIconButton
from .widgets.py_line_edit import PyLineEdit
from ..utils import *
from ..operation import SineSetupMain
from ..pipeline_helper import USER_PATH

_dir_name = os.path.dirname(__file__)
icon_dir = os.path.join(_dir_name, "images", "svg_icons")

# TODO : option btn to toggle language
_L = LANGUAGE = 0  # 0 for English, 1 for Japanese

COLOR_INDEX = {}
for __COLOR in range(2, 32):
    COLOR_INDEX[__COLOR] = [round(X * 255.0) for X in cmds.colorIndex(__COLOR, q=1)]


class SineUI(MainWindow):
    def __init__(self):
        super(SineUI, self).__init__()
        self.start_file_path = USER_PATH
        self.source_checker = []
        self.settings_dialog = SineSettingsDialog()
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        font = QtGui.QFont()
        font.setPointSize(6 * DPI_SCALE)
        font.setBold(True)
        text = [
            # "Please select the namespace of the object to be applied",
            "（Namespace-related functions are not yet done）",
            # "適用するオブジェクトのネームスペースを選択してください",
            "（まだネームスペース関係の機能はしません）"]
        self.top_label = QtWidgets.QLabel(text[_L])
        self.top_label.setAlignment(QtCore.Qt.AlignCenter)
        self.top_label.setFont(font)
        self.top_label.setMargin(14 * DPI_SCALE)

        text = ["Add to List", "リストに追加"]
        self.left_top_btn = PyPushButton(text[_L])
        text = ["Remove from List", "リストから削除"]
        self.left_top_btn2 = PyPushButton(text[_L])
        text = ["Import Preset", "Preset導入"]
        self.left_top_btn3 = PyIconButton(icon_path=Functions.set_svg_icon("icon_folder_open.svg"),
                                          parent=self.parent(),
                                          app_parent=None,
                                          tooltip_text=text[_L],
                                          bg_color_hover="#1e2229",
                                          width=60
                                          )
        text = ["Export Preset", "Preset出力"]
        self.left_top_btn4 = PyIconButton(icon_path=Functions.set_svg_icon("icon_save.svg"),
                                          parent=self.parent(),
                                          app_parent=None,
                                          tooltip_text=text[_L],
                                          bg_color_hover="#1e2229",
                                          width=60
                                          )
        text = ["Delete Selected Setup", "選択セットアップを削除"]
        self.right_top_btn = PyPushButton(text[_L])

        self.name_spacing_cbx = PyCombobox()
        cmds.namespace(setNamespace=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        namespaces = list((set(namespaces) - {'UI', 'shared'}))
        namespaces.insert(0, "-- root -- (no name space)")
        self.name_spacing_cbx.addItems(namespaces)

        self.source_lw = PyListWidget()
        self.source_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Create Setup", "セットアップを作成"]
        self.left_btn = PyPushButton(text[_L])

        self.master_lw = PyListWidget()
        self.master_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Clear Sets", "セットをクリア"]
        self.right_btn = PyPushButton(text[_L])

    def create_layout(self):

        # left
        left_layout = QtWidgets.QVBoxLayout()

        top_left_btn_layout = QtWidgets.QHBoxLayout()
        top_left_btn_layout.addWidget(self.left_top_btn, 2)
        top_left_btn_layout.addWidget(self.left_top_btn2, 2)
        top_left_btn_layout.addWidget(self.left_top_btn3, 1)
        top_left_btn_layout.addWidget(self.left_top_btn4, 1)

        source_list_layout = QtWidgets.QVBoxLayout()
        source_list_layout.addWidget(self.source_lw)

        left_btn_layout = QtWidgets.QHBoxLayout()
        left_btn_layout.addWidget(self.left_btn)

        left_layout.addLayout(top_left_btn_layout)
        left_layout.addLayout(source_list_layout)
        left_layout.addLayout(left_btn_layout)

        # right
        right_layout = QtWidgets.QVBoxLayout()

        top_right_btn_layout = QtWidgets.QHBoxLayout()
        top_right_btn_layout.addWidget(self.right_top_btn)

        master_list_layout = QtWidgets.QVBoxLayout()
        master_list_layout.addWidget(self.master_lw)

        right_btn_layout = QtWidgets.QHBoxLayout()
        right_btn_layout.addWidget(self.right_btn)

        right_layout.addLayout(top_right_btn_layout)
        right_layout.addLayout(master_list_layout)
        right_layout.addLayout(right_btn_layout)

        # main
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.top_label)
        main_layout.addWidget(self.name_spacing_cbx)
        main_layout.addLayout(top_left_btn_layout)

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.addLayout(left_layout, 7)
        horizontal_layout.addLayout(right_layout, 3)
        main_layout.addLayout(horizontal_layout)

        self.content_layout.addLayout(main_layout, -2)

        # CREDITS / BOTTOM APP FRAME
        # ///////////////////////////////////////////////////////////////
        self.credits_frame = QtWidgets.QFrame()
        self.credits_frame.setMinimumHeight(26)
        self.credits_frame.setMaximumHeight(26)
        # CREATE LAYOUT
        self.credits_layout = QtWidgets.QHBoxLayout(self.credits_frame)
        self.credits_layout.setContentsMargins(0, 0, 0, 0)

        # ADD CUSTOM WIDGET CREDITS
        self.credits = PyCredits(
            bg_two=self.themes["app_color"]["bg_two"],
            copyright=self.settings["copyright"],
            version=self.settings["version"],
            font_family=self.settings["font"]["family"],
            text_size=self.settings["font"]["text_size"],
            text_description_color=self.themes["app_color"]["text_description"]
        )

        #  ADD TO LAYOUT
        self.content_layout.addWidget(self.credits)

    def create_connections(self):
        self.left_top_btn.clicked.connect(self.add_source)
        self.left_top_btn2.clicked.connect(self.remove_source)
        self.left_top_btn3.clicked.connect(self.import_source)
        self.left_top_btn4.clicked.connect(self.export_source)
        self.left_btn.clicked.connect(self.add_master_item)

        self.right_top_btn.clicked.connect(self.delete_selected_setup)
        self.right_btn.clicked.connect(self.clear_related_sets)

        self.source_lw.itemDoubleClicked.connect(self.select_source_item)
        self.master_lw.itemDoubleClicked.connect(self.select_master_item)

    def select_source_item(self):
        items = [ast.literal_eval(i.text()) for i in self.source_lw.selectedItems()][0]
        pm.select(items)

    def select_master_item(self):
        item = [i.text() + "_MCtl" for i in self.master_lw.selectedItems()][0]
        pm.select(item)

    def add_source(self, obj=None):
        """ add item to ui list, get warnings if obj already assigned """
        if not obj:
            obj = pm.ls(os=1, o=1)
        if not obj:  # maybe add a condition to limit len(sl)>1 ?
            return
        if self.source_checker:
            for i in obj:
                if i in self.source_checker:
                    text = ["object '{}' already assigned".format(i),
                            "オブジェクト '{}' はすでに割り当てられています".format(i)]
                    return pm.warning(ensure_text(text[_L]))
        text = str([str(i.name()) for i in obj])
        self.source_lw.addItem(text)
        [self.source_checker.append(i) for i in obj if i not in self.source_checker]

    def remove_source(self):
        """ remove selected item from ui"""
        if not self.source_lw.selectedIndexes():
            return
        indices = [(i.row(), i) for i in self.source_lw.selectedIndexes()]
        indices.sort(key=lambda i: i[0], reverse=True)
        for i in indices:
            items = ast.literal_eval(self.source_lw.itemFromIndex(i[1]).text())
            [self.source_checker.remove(_i) for _i in items if _i in self.source_checker]
            self.source_lw.takeItem(i[0])

    def import_source(self):
        filters = "Sine Tool Config (*%s)" % ".sineConfig"
        file, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select Config File",
                                                                      self.start_file_path,
                                                                      filters,
                                                                      filters)
        # if file exists, load config
        if os.path.exists(file):
            file_name = os.path.basename(file)
            self.start_file_path = os.path.dirname(file)
            f = open(file)
            config = json.load(f)
            # then check if config is able to pass into ListWidget
            all_val = []
            [all_val.extend(i) for i in list(config.values())]
            config_valid = all([len(pm.ls(i)) == 1 for i in all_val])
            if not config_valid:
                not_in_scene = [i for i in all_val if not pm.objExists(i)]
                name_duped = [i for i in all_val if len(pm.ls(i)) > 1]
                if not_in_scene:
                    text = ["{} not in the scene ".format(not_in_scene),
                            "{} はシーン内に存在しません".format(not_in_scene)]
                    pm.warning(ensure_text(text[_L]))
                if name_duped:
                    text = ["{} has duplicated names".format(name_duped),
                            "{} は名前が重複している".format(name_duped)]
                    pm.warning(ensure_text(text[_L]))
                return
            self.source_lw.clear()
            self.source_checker = []
            self.settings_dialog.line_edit.setText(file_name.split(".")[0])
            for chain in config.values():
                chain_nodes = [pm.PyNode(i) for i in chain]
                self.add_source(chain_nodes)

    def export_source(self):
        config_description = {}
        for i in range(self.source_lw.count()):
            config_description[i] = ast.literal_eval(self.source_lw.item(i).text())
        filters = "Sine Tool Config (*%s)" % ".sineConfig"
        file, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Select Config File",
                                                                      self.start_file_path,
                                                                      filters,
                                                                      filters)
        with open(file, 'w') as f:
            json.dump(config_description, f)
        if os.path.exists(file):
            self.start_file_path = os.path.dirname(file)

    def add_master_item(self):
        """ add master item to the ui list """
        if not self.source_lw.selectedItems():
            return
        selected_sets = [i.text() for i in self.source_lw.selectedItems()]

        # collect data
        elements = {}
        matrices = {}
        for i in selected_sets:
            current_index = len(list(elements.keys()))
            elements[current_index] = ast.literal_eval(i)
            elements[current_index].reverse()
            try:
                pynodes = [pm.PyNode(j) for j in elements[current_index]]
            except pm.MayaNodeError:
                text = ["failed to get pynodes from list. index:{}".format(current_index),
                        "{}番のリストからの pynode の取得に失敗しました".format(current_index)]
                return pm.warning(ensure_text(text[_L]))
            matrices[current_index] = [pm.xform(i, q=1, m=1, ws=1) for i in pynodes]

        self.settings_dialog.show()
        if self.settings_dialog.exec_() == QtWidgets.QDialog.Accepted:
            master = SineSetupMain(elements, matrices, self.settings_dialog.config)
            self.master_lw.addItem("Sine_" + master.config["name"])

    def delete_selected_setup(self):
        if self.master_lw.selectedItems():
            [pm.delete(i.text()) for i in self.master_lw.selectedItems()]
        if pm.objExists("Sine_Grp") and not pm.PyNode("Sine_Grp").getChildren():
            pm.delete("Sine_Grp")

    @staticmethod
    def clear_related_sets():
        sets = pm.ls("Sine*Sets", type="objectSet")
        pm.delete(sets)

    def closeEvent(self, event):
        # super(SineUI, self).closeEvent(event)
        self.settings_dialog.close()
        self.close()


class SineSettingsDialog(SubWindow):
    def __init__(self):
        super(SineSettingsDialog, self).__init__()
        self.raw_color_value = None
        self.use_index = None
        self.init()
        # self.objects = objects

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.titleBar.set_title("Sine Ctrl Settings")
        self.setWindowTitle("Sine Ctrl Settings")
        # self.setStyleSheet(STYLE)
        self.setFixedSize(380 * DPI_SCALE, 352 * DPI_SCALE)

    def init(self):
        self.use_index = 17  # 0(false) ~ 31
        self.raw_color_value = cmds.colorIndex(17, q=1)  # rgb : 0~1
        self.config = dict(
            name="untitled",
            fk_size=1.0,
            ik_size=1.0,
            ik_count=1,
            use_index=self.use_index,
            color=self.raw_color_value
        )

    def create_widgets(self):
        font = QtGui.QFont()
        font.setPointSize(6 * DPI_SCALE)
        font.setBold(True)
        font.setFamily("Segoe UI")
        text = ["Tip : Key Frames will be deleted", "ヒント：キーフレームは削除されます"]
        self.label = QtWidgets.QLabel(text[_L])
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("color:orange;")
        self.label.setFont(font)
        self.label.setMargin(20)
        text = ["Please enter the Ctrl Name", "コントローラの名前を指定してください"]
        # self.label2 = QtWidgets.QLabel(text[_L])
        # self.label2.setAlignment(QtCore.Qt.AlignCenter)
        # self.label2.setFont(font)
        self.line_edit = PyLineEdit(place_holder_text=text[_L])
        exp = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*$")
        self.line_edit.setValidator(QtGui.QRegExpValidator(exp))
        text = ["Create", "作成"]
        self.confirm_btn = PyPushButton(text[_L])
        text = ["Cancel", "キャンセル"]
        self.cancel_btn = PyPushButton(text[_L])

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.label)
        # main_layout.addWidget(self.label2)
        main_layout.addWidget(self.line_edit)
        # SUB CONTENTS
        sub_content_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        font = QtGui.QFont()
        font.setPointSize(6 * DPI_SCALE)
        font.setFamily("Segoe UI")

        # # SLIDERS
        self.fk_size_slider = FloatSliderGroup()
        self.fk_size_slider.set_range(0.1, 10.0)
        self.fk_size_slider.set_value(1.0)
        self.ik_size_slider = FloatSliderGroup()
        self.ik_size_slider.set_range(0.1, 10.0)
        self.ik_size_slider.set_value(1.0)
        self.ik_count_slider = IntSliderGroup()
        self.ik_count_slider.set_range(2, 10)
        text = ["FK Size :　", "FK Ctrl の サイズ　:　"]
        form_layout.addRow(text[_L], self.fk_size_slider)
        form_layout.labelForField(self.fk_size_slider).setFont(font)
        text = ["IK Size :　", "IK Ctrl の サイズ　:　"]
        form_layout.addRow(text[_L], self.ik_size_slider)
        form_layout.labelForField(self.ik_size_slider).setFont(font)
        text = ["IK Count :　", "IK Ctrl の 数　:　"]
        form_layout.addRow(text[_L], self.ik_count_slider)
        form_layout.labelForField(self.ik_count_slider).setFont(font)

        # # COLOR BUTTONS
        self.color_visual_btn = QtWidgets.QPushButton()
        self.color_visual_btn.setMaximumHeight(20 * DPI_SCALE)
        q_color = [round(i * 255.0) for i in self.raw_color_value]
        visual_name = QtGui.QColor(*q_color).name()
        _style = "QPushButton#pushButton {background-color: %s;}" % visual_name
        self.color_visual_btn.setStyleSheet(_style)
        self.color_visual_btn.clicked.connect(self.on_color_btn_clicked)

        text = ["Ctl Color :　", "Ctrlの色指定　:　"]
        null = QtWidgets.QLabel()
        form_layout.addRow(text[_L], null)
        form_layout.labelForField(null).setFont(font)

        self.index_grp = ColorIndexGroup()
        self.index_grp.setMaximumHeight(80 * DPI_SCALE)
        self.index_grp.btn_clicked.connect(self.set_color_index)
        self.index_grp.color_btns[15].click()
        sub_content_layout.addLayout(form_layout)
        sub_content_layout.addWidget(self.color_visual_btn)
        sub_content_layout.addWidget(self.index_grp)

        self.content_widget = QtWidgets.QFrame()
        self.content_widget.setLayout(sub_content_layout)

        main_layout.addWidget(self.content_widget)
        main_layout.addStretch()

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.confirm_btn)

        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)
        self.content_layout.addLayout(main_layout)

    def create_connections(self):
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.cancel_btn.clicked.connect(self.reject)
        # self.collapse_layout.on_clicked.connect(self.change_size)
        # self.coll.on_clicked.connect(self.change_size)

    def on_color_btn_clicked(self):
        current_color = self.raw_color_value
        _color = cmds.colorEditor(rgb=current_color).split()[:-1]
        if _color == ['0', '0', '0']:  # check if the colorEditor dialog was canceled
            return
        raw_color = [float(i) for i in _color]
        raw_q_color = [round(float(i) * 255.0) for i in _color]
        cc_color = [round(float(i) * 255.0) for i in cmds.colorManagementConvert(toDisplaySpace=raw_color)]
        visual_name = QtGui.QColor(*cc_color).name()
        print(cc_color)
        self.color_visual_btn.setStyleSheet("background-color: {};".format(visual_name))
        self.raw_color_value = [i / 255.0 for i in QtGui.QColor(*raw_q_color).getRgb()[:-1]]
        self.use_index = False

    def set_color_index(self):
        color = QtGui.QColor(self.index_grp.current_cc_color)
        self.color_visual_btn.setStyleSheet("background-color: {};".format(color.name()))
        self.raw_color_value = [i / 255.0 for i in color.getRgb()[:-1]]
        self.use_index = self.index_grp.current_index

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = config

    def on_confirm(self):
        if not self.line_edit.text():
            text = ["Please Set a Ctrl Name!", "コントローラーの名前を指定してください"]
            return pm.warning(ensure_text(text[_L]))
        self.config = dict(
            name=self.line_edit.text(),
            fk_size=self.fk_size_slider.value(),
            ik_size=self.ik_size_slider.value(),
            ik_count=self.ik_count_slider.value(),
            use_index=self.use_index,
            color=[i for i in self.raw_color_value]
        )
        self.accept()

    def mousePressEvent(self, event):
        # to de-focus the lineEdit
        focused_widget = QtWidgets.QApplication.focusWidget()
        if isinstance(focused_widget, PyLineEdit):
            focused_widget.clearFocus()
        QtWidgets.QMainWindow.mousePressEvent(self, event)
        if event.buttons() == QtCore.Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()


class ColorIndexGroup(QtWidgets.QWidget):
    btn_clicked = QtCore.Signal()

    def __init__(self):
        super(ColorIndexGroup, self).__init__()
        self.current_index = None
        self.current_cc_color = None

        self.color_index = COLOR_INDEX
        self.cc_color_index = {}

        main_layout = FlowLayout(self)
        # main_layout = QtWidgets.QVBoxLayout(self)
        self.color_btns = []
        for i in range(2, 32):
            box = self.colorBox(i)
            main_layout.addWidget(box)
            self.color_btns.append(box)

    @staticmethod
    def updateWidgetStyleSheet(sourceWidget, rgb):
        color = [round(i * 255.0) for i in cmds.colorManagementConvert(toDisplaySpace=rgb)]
        name = QtGui.QColor(*color).name()
        sourceWidget.setStyleSheet("background-color: {};".format(name))
        return name

    def colorBox(self, index_number):
        if not isinstance(index_number, int):
            return
        if index_number not in self.color_index.keys():
            return
        raw_color = [c / 255.0 for c in self.color_index[index_number]]

        box = QtWidgets.QPushButton()
        name = self.updateWidgetStyleSheet(box, raw_color)
        self.cc_color_index[index_number] = name
        box.clicked.connect(partial(self.on_btn_clicked, index_number))
        box.setMaximumSize(30 * DPI_SCALE, 18 * DPI_SCALE)
        return box

    def on_btn_clicked(self, index):
        self.current_index = index
        self.current_cc_color = self.cc_color_index[index]
        self.btn_clicked.emit()
