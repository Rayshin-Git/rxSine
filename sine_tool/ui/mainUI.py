#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import ast
import glob
import json
from functools import partial

from maya import cmds

from .core.functions import Functions
from .templates.main_window import MainWindow, SubWindow
from .templates.widgets import IntSliderGroup, FloatSliderGroup, FlowLayout
from .widgets.py_combobox import PyCombobox
from .widgets.py_credits_bar import PyCredits
from .widgets.py_icon_button import PyIconButton
from .widgets.py_line_edit import PyLineEdit
from .widgets.py_list_widget import PyListWidget
from .widgets.py_push_button import PyPushButton
from ..utils import *
from ..utils.helper import disable_undo
from ..utils.pipeline_helper import PIPLINE_AVAILABLE, USER_PATH, PROJECT_NAME, USER_NAME
from ..utils.py_compatible import ensure_text, string_types
from ..operation import SineSetupMain

MODULE_DIR = os.path.dirname(os.path.normpath(__file__)).replace("\\", "/")
if not PIPLINE_AVAILABLE:
    CONFIG_DIR = os.path.join(MODULE_DIR, "_config").replace("\\", "/")
else:
    CONFIG_DIR = os.path.join(MODULE_DIR, "_config", PROJECT_NAME, USER_NAME).replace("\\", "/")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json").replace("\\", "/")

_dir_name = os.path.dirname(__file__)
icon_dir = os.path.join(_dir_name, "images", "svg_icons")

COLOR_INDEX = {}
for __COLOR in range(2, 32):
    COLOR_INDEX[__COLOR] = [round(X * 255.0) for X in cmds.colorIndex(__COLOR, q=1)]


class SineUI(MainWindow):
    def __init__(self):
        super(SineUI, self).__init__()
        self.file_list = None
        self.sineConfig_file_path = USER_PATH
        self.source_checker = []
        self.settings_dialog = SineSettingsDialog()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.search_existing_setups()
        self.restore_config()
        self.make_tooltips_toplayer()

        print(self.titleBar.height())

    def create_widgets(self):
        font = QtGui.QFont()
        font.setPointSize(self.settings["font"]["text_size"] * 1.2)
        font.setBold(True)
        text = [
            "Tips : you can override namespaces by using the UI below",
            "Tips : 下のUIでnamespaceを上書きすることができます。"]
        self.top_label = QtWidgets.QLabel(text[self._L])
        self.top_label.setAlignment(QtCore.Qt.AlignCenter)
        self.top_label.setFont(font)
        self.top_label.setMargin(14 * DPI_SCALE)

        text = ["Add to List", "リストに追加"]
        self.left_top_btn = PyPushButton(text[self._L])
        text = ["Remove from List", "リストから削除"]
        self.left_top_btn2 = PyPushButton(text[self._L])
        text = ["Preset Tab", "Preset Tab"]
        offsetPos = [0, 0] if DPI_SCALE == 1 else [0, 40 * DPI_SCALE]
        self.left_top_btn3 = PyIconButton(icon_path=Functions.set_svg_icon("icon_settings.svg"),
                                          parent=self.parent(),
                                          app_parent=None,
                                          tooltip_text=text[self._L],
                                          bg_color_hover="#1e2229",
                                          width=60,
                                          height=self.left_top_btn.height(),
                                          context_color=self.themes["app_color"]["context_pressed"],
                                          bg_color_pressed=self.themes["app_color"]["dark_four"],
                                          # offsetPos=offsetPos
                                          )
        text = ["Export Preset", "Preset出力"]
        self.left_top_btn4 = PyIconButton(icon_path=Functions.set_svg_icon("icon_save.svg"),
                                          parent=self.parent(),
                                          app_parent=None,
                                          tooltip_text=text[self._L],
                                          bg_color_hover="#1e2229",
                                          width=60,
                                          height=self.left_top_btn.height()
                                          )
        text = ["Delete Selected Setup", "選択セットアップを削除"]
        self.right_top_btn = PyPushButton(text[self._L])

        self.name_spacing_cbx = PyCombobox()
        pm.namespace(setNamespace=':')
        namespaces = pm.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        namespaces = list((set(namespaces) - {'UI', 'shared'}))
        namespaces.insert(0, "-- root --")
        self.name_spacing_cbx.addItems(namespaces)

        self.source_lw = PyListWidget()
        self.source_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Create Setup", "セットアップを作成"]
        self.left_btn = PyPushButton(text[self._L])

        self.master_lw = PyListWidget()
        self.master_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Clear Sets", "セットをクリア"]
        self.right_btn = PyPushButton(text[self._L])

    def create_layout(self):

        # left
        left_layout = QtWidgets.QVBoxLayout()

        top_left_btn_layout = QtWidgets.QHBoxLayout()
        top_left_btn_layout.addWidget(self.left_top_btn, 2)
        top_left_btn_layout.addWidget(self.left_top_btn2, 2)
        top_left_btn_layout.addWidget(self.left_top_btn3, 1)
        # top_left_btn_layout.addWidget(self.left_top_btn4, 1)

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
        # self.content_layout.addWidget(self.credits)
        self.main_layout.addWidget(self.credits)

    def create_connections(self):
        self.left_top_btn.clicked.connect(self.add_source)
        self.left_top_btn2.clicked.connect(self.remove_source)
        # self.left_top_btn3.clicked.connect(self.import_source)
        self.left_top_btn3.clicked.connect(self.toggle_right_column)
        self.left_top_btn3.clicked.connect(self.left_top_btn3.toggle_active)
        # self.left_top_btn4.clicked.connect(self.export_source)
        self.left_btn.clicked.connect(self.add_master_item)

        self.right_top_btn.clicked.connect(self.delete_selected_setup)
        self.right_btn.clicked.connect(self.clear_related_sets)

        self.source_lw.itemDoubleClicked.connect(self.select_source_item)
        self.master_lw.itemDoubleClicked.connect(self.select_master_item)
        self.name_spacing_cbx.activated.connect(self.update_namespaces)

        # RIGHT COLUMN
        self.right_column.setPath_btn.clicked.connect(self.set_IO_path)
        self.right_column.path_le.returnPressed.connect(self.set_IO_path_LE)
        self.right_column.export_btn.clicked.connect(self.export_source)
        self.right_column.file_lst.itemClicked.connect(self.load_config_from_selected_item)

    def closeEvent(self, event):
        # super(SineUI, self).closeEvent(event)
        self.settings_dialog.close()
        self.store_config_file()
        self.close()

    def make_tooltips_toplayer(self):
        self.titleBar.minimize_button._tooltip.raise_()
        self.titleBar.maximize_restore_button._tooltip.raise_()
        self.titleBar.close_button._tooltip.raise_()

        self.right_column.setPath_btn._tooltip.raise_()
        self.right_column.export_btn._tooltip.raise_()

    # NON UI RELATED METHODS BELOW
    def search_existing_setups(self):
        existing = []
        if len(pm.ls("Sine_Grp")) == 1 and pm.PyNode("Sine_Grp").getChildren():
            for ele_grp in pm.PyNode("Sine_Grp").getChildren():
                MCtl = pm.PyNode(ele_grp.name() + "_MCtl") if pm.objExists(ele_grp.name() + "_MCtl") else None
                if MCtl is not None and MCtl in ele_grp.getChildren():
                    annotation = pm.PyNode(ele_grp.name() + "_annotation") if pm.objExists(
                        ele_grp.name() + "_annotation") else None
                    if annotation is not None and annotation in MCtl.getChildren():
                        existing.append(ele_grp.name())

        if existing:
            self.master_lw.addItems(existing)

    def select_source_item(self):
        items = [ast.literal_eval(i.text()) for i in self.source_lw.selectedItems()][0]
        pm.select(pm.ls(items))
        not_in_scene = [i for i in items if not pm.objExists(i)]
        if not_in_scene:
            text = ["failed to get pynodes from scene:\n{}".format(not_in_scene),
                    "シーンからの pynode の取得に失敗しました:\n{}".format(not_in_scene)]
            pm.warning(ensure_text(text[self._L]))

    def select_master_item(self):
        item = [i.text() + "_MCtl" for i in self.master_lw.selectedItems()][0]
        pm.select(item)

    def add_source(self, objLs=None):
        """ add item to ui list, get warnings if obj already assigned """
        from_scene = False
        if not objLs:
            from_scene = True
            objLs = pm.ls(os=1, o=1)
        if len(objLs) < 2:
            text = ["must have at least 2 objs",
                    "少なくとも2つのオブジェが必要"]
            return pm.warning(ensure_text(text[self._L]))
        if self.source_checker:
            for i in objLs:
                if i in self.source_checker:
                    text = ["object '{}' already assigned".format(i),
                            "オブジェクト '{}' はすでに割り当てられています".format(i)]
                    return pm.warning(ensure_text(text[self._L]))
        # text = str([str(i.name()) for i in objLs])
        text = str([i for i in objLs]) if not from_scene else str([str(i.name()) for i in objLs])
        self.source_lw.addItem(text)
        [self.source_checker.append(i) for i in objLs if i not in self.source_checker]

    def update_namespaces(self):
        namespace = self.name_spacing_cbx.currentText() if self.name_spacing_cbx.currentIndex() != 0 else ""
        namespace = str(namespace)
        count = self.source_lw.count()
        if not count:
            return
        for i in range(count):
            item = self.source_lw.item(i)
            item_to_list = ast.literal_eval(item.text())
            new_list = [namespace + ":" + i.split(":")[-1] for i in item_to_list] \
                if namespace else [i.split(":")[-1] for i in item_to_list]
            item.setText(str(new_list))

    def remove_source(self):
        """ remove selected item from ui"""
        if not self.source_lw.selectedIndexes():
            return
        indices = [(i.row(), i) for i in self.source_lw.selectedIndexes()]
        indices.sort(key=lambda k: k[0], reverse=True)
        for i in indices:
            items = ast.literal_eval(self.source_lw.itemFromIndex(i[1]).text())
            [self.source_checker.remove(j) for j in items if j in self.source_checker]
            self.source_lw.takeItem(i[0])

    def add_master_item(self):
        """ add master item to the ui list """
        if not self.source_lw.selectedItems():
            return
        selected_items = [i.text() for i in self.source_lw.selectedItems()]

        # first, check if un-existing node in data
        # collect data
        elements = {}
        for i in selected_items:
            current_index = len(list(elements.keys()))
            elements[current_index] = ast.literal_eval(i)
            elements[current_index].reverse()
            try:
                # run single test first
                pynodes = [pm.PyNode(j) for j in elements[current_index]]
            except pm.MayaNodeError:
                # when error detected check all element
                all_ele = []
                for set_ in selected_items:
                    all_ele.extend(ast.literal_eval(set_))
                not_in_scene = [i for i in all_ele if not pm.objExists(i)]
                text = ["failed to get pynodes from scene:\n{}".format(not_in_scene),
                        "シーンからの pynode の取得に失敗しました:\n{}".format(not_in_scene)]
                return pm.warning(ensure_text(text[self._L]))
        # second, if all existing, then check if they are already assigned
        # collect data
        elements = {}
        matrices = {}
        for i in selected_items:
            current_index = len(list(elements.keys()))
            elements[current_index] = ast.literal_eval(i)
            elements[current_index].reverse()
            try:
                # run single test first
                pynodes = [pm.PyNode(j) for j in elements[current_index]]
            except pm.MayaNodeError:
                # when error detected check all element
                all_ele = []
                for set_ in selected_items:
                    all_ele.extend(ast.literal_eval(set_))
                not_in_scene = [i for i in all_ele if not pm.objExists(i)]
                text = ["failed to get pynodes from scene:\n{}".format(not_in_scene),
                        "シーンからの pynode の取得に失敗しました:\n{}".format(not_in_scene)]
                return pm.warning(ensure_text(text[self._L]))
            else:
                if pm.ls('Sine_Main_Bake_Sets'):
                    # run single test first
                    ele_in_sets = []
                    sub_sets = [i for i in pm.ls('Sine_Main_Bake_Sets')[0].members()]
                    _error = False
                    for subset in sub_sets:
                        for item in elements[current_index]:
                            connections = pm.listConnections(pm.PyNode(item).translateX, plugs=True,
                                                             connections=True)
                            connections_ = []
                            for cs in connections:
                                if isinstance(cs, (list, tuple)):
                                    for c in cs:
                                        connections_.append(c)
                                else:
                                    connections_.append(cs)
                            hasCns = any(['{}_tempCns'.format(item) in i.name() for i in connections_])
                            if subset.isMember(item) and hasCns:
                                _error = True
                                break

                    if _error:
                        # when error detected check all element
                        all_ele = []
                        for set_ in selected_items:
                            all_ele.extend(ast.literal_eval(set_))
                        ele_hasCns = []
                        for item in all_ele:
                            connections = pm.listConnections(pm.PyNode(item).translateX, plugs=True,
                                                             connections=True)
                            connections_ = []
                            for cs in connections:
                                if isinstance(cs, (list, tuple)):
                                    for c in cs:
                                        connections_.append(c)
                                else:
                                    connections_.append(cs)
                            hasCns = any(['{}_tempCns'.format(item) in i.name() for i in connections_])
                            if hasCns:
                                ele_hasCns.append(item)
                        for subset in sub_sets:
                            # if isinstance(subset, string_types):
                            #     subset = pm.PyNode(subset)
                            subset_n = [i.name() for i in subset.members()]
                            ele_in_sets.extend(subset_n)
                        already_assigned = [i for i in ele_hasCns if i in ele_in_sets]
                        text = ["some elements already assigned:\n{}".format(already_assigned),
                                "一部の項目はすでに割り当てられています:\n{}".format(already_assigned)]
                        return pm.warning(ensure_text(text[self._L]))

            matrices[current_index] = [pm.xform(i, q=1, m=1, ws=1) for i in pynodes]

        self.settings_dialog.show()
        if self.settings_dialog.exec_() == QtWidgets.QDialog.Accepted:
            master = self._sine_setup(elements, matrices, self.settings_dialog.config)
            slaves = []
            [slaves.extend(i) for i in master.slaves.values()]
            pm.cutKey(pm.ls(slaves))
            self.master_lw.addItem("Sine_" + master.config["name"])

    @disable_undo
    def _sine_setup(self, elements, matrices, config):
        master = SineSetupMain(elements, matrices, config)
        return master

    def delete_selected_setup(self):
        if self.master_lw.selectedItems():
            rev_id = [i.row() for i in self.master_lw.selectedIndexes()]
            rev_id.sort(reverse=True)
            for i in rev_id:
                item = self.master_lw.item(i)
                if pm.objExists(item.text() + "_MCtl"):
                    pm.delete(pm.PyNode(item.text() + "_MCtl").getParent())
                if pm.objExists(item.text() + "_Bake_Sets"):
                    pm.PyNode(item.text() + "_Bake_Sets").rename(item.text() + "_Bake_Sets_old")
                self.master_lw.takeItem(i)

        if pm.objExists("Sine_Grp") and not pm.PyNode("Sine_Grp").getChildren():
            pm.delete("Sine_Grp")

    @staticmethod
    def clear_related_sets():
        sets = pm.ls("Sine*Sets", type="objectSet") + pm.ls("Sine*Sets_old*", type="objectSet")
        pm.delete(sets)

    def set_IO_path(self, dir=""):
        if not dir or not os.path.exists(ensure_text(dir)):
            _dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Config Folder",
                                                              self.sineConfig_file_path)
        else:
            _dir = ensure_text(dir)
        # if dir exists, load config to ui selected namespace
        if os.path.isdir(_dir):
            self.sineConfig_file_path = _dir
            self.right_column.path_le.setText(self.sineConfig_file_path)
            self.update_sineConfig_filesList()

    def set_IO_path_LE(self):
        self.left_top_btn3.setDefault(False)
        _dir = self.right_column.path_le.text()
        # if file exists, load config to ui selected namespace
        if os.path.isdir(_dir):
            self.sineConfig_file_path = _dir
            self.update_sineConfig_filesList()
        else:
            if os.path.isdir(self.sineConfig_file_path):
                self.right_column.path_le.setText(self.sineConfig_file_path)
            else:
                self.right_column.path_le.setText("")

    def update_sineConfig_filesList(self):
        self.right_column.file_lst.clear()
        path = self.sineConfig_file_path
        if not os.path.isdir(path):
            return
        file_type = "*.sineConfig"
        self.file_list = glob.glob(os.path.join(path, file_type))
        for file in self.file_list:
            file_name = "".join(os.path.basename(file).split(".")[:-1])
            self.right_column.file_lst.addItem(file_name)
        self.right_column.setFocus()

    def load_config_from_selected_item(self):
        index = self.right_column.file_lst.currentIndex().row()
        config_file = self.file_list[index]
        if os.path.exists(config_file):
            f = open(config_file)
            basename = os.path.basename(config_file)
            name_without_extension = os.path.splitext(basename)[0]
            self.settings_dialog.line_edit.setText(name_without_extension)
            config = json.load(f)
            # self.source_lw.addItems(config)
            self.source_lw.clear()
            self.source_checker = []
            for i in config:
                i_ = [str(chd) for chd in i]
                self.add_source(i_)

    def export_source(self):
        config_description = []
        for i in range(self.source_lw.count()):
            node_strings = ast.literal_eval(self.source_lw.item(i).text())
            # config_description.append([pm.PyNode(j).stripNamespace() for j in node_strings])
            config_description.append(node_strings)
        if not config_description:
            text = ["no value to export!", "エクスポート出来るデータが存在しない"]
            return pm.warning(ensure_text(text[self._L]))
        filters = "Sine Tool Config (*%s)" % ".sineConfig"
        file, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Select Config File",
                                                                      self.sineConfig_file_path,
                                                                      filters,
                                                                      filters)
        if not file:
            return
        with open(file, 'w') as f:
            json.dump(config_description, f, indent=4)
        dir = os.path.dirname(file)
        self.set_IO_path(dir)
        self.update_sineConfig_filesList()

    def store_config_file(self):
        if not self.sineConfig_file_path or not os.path.exists(self.sineConfig_file_path):
            return
        config_description = dict(configPath=self.sineConfig_file_path,
                                  )
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            pm.displayInfo("config folder created : {}".format(CONFIG_DIR))
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_description, f)

    def restore_config(self):
        if os.path.exists(CONFIG_FILE):
            f = open(CONFIG_FILE)
            config = json.load(f)
            try:
                self.sineConfig_file_path = str(config["configPath"])
                self.right_column.path_le.setText(self.sineConfig_file_path)
                self.update_sineConfig_filesList()
            except:
                pass


class SineSettingsDialog(SubWindow):
    def __init__(self):
        super(SineSettingsDialog, self).__init__()
        self.raw_color_value = None
        self.use_index = None
        self.init()

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.titleBar.set_title("Sine Ctrl Settings")
        self.setWindowTitle("Sine Ctrl Settings")
        if DPI_SCALE == 1.5:
            self.setFixedSize(380 * DPI_SCALE, 350 * DPI_SCALE)
        else:
            self.setFixedSize(420 * DPI_SCALE, 390 * DPI_SCALE)

        self.make_tooltips_toplayer()

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
        font.setPointSize(self.settings["font"]["text_size"] * 1.2)
        font.setBold(True)
        font.setFamily("Segoe UI")
        text = ["Undo Queue,Key Frames will be deleted", "Undo Queueとキーフレームが削除されます"]
        self.label = QtWidgets.QLabel(text[self._L])
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("color:orange;")
        self.label.setFont(font)
        self.label.setMargin(20)
        text = ["Please enter the Ctrl Name", "コントローラの名前を指定してください"]

        self.line_edit = PyLineEdit(place_holder_text=text[self._L])
        exp = QtCore.QRegExp("^[a-zA-Z][a-zA-Z0-9_]*$")
        self.line_edit.setValidator(QtGui.QRegExpValidator(exp))
        text = ["Create", "作成"]
        self.confirm_btn = PyPushButton(text[self._L])
        text = ["Cancel", "キャンセル"]
        self.cancel_btn = PyPushButton(text[self._L])

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.line_edit)
        # SUB CONTENTS
        sub_content_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        font = QtGui.QFont()
        font.setPointSize(self.settings["font"]["text_size"])
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
        form_layout.addRow(text[self._L], self.fk_size_slider)
        form_layout.labelForField(self.fk_size_slider).setFont(font)
        text = ["IK Size :　", "IK Ctrl の サイズ　:　"]
        form_layout.addRow(text[self._L], self.ik_size_slider)
        form_layout.labelForField(self.ik_size_slider).setFont(font)
        text = ["IK Count :　", "IK Ctrl の 数　:　"]
        form_layout.addRow(text[self._L], self.ik_count_slider)
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
        form_layout.addRow(text[self._L], null)
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

    def on_color_btn_clicked(self):
        current_color = self.raw_color_value
        _color = cmds.colorEditor(rgb=current_color).split()[:-1]
        if _color == ['0', '0', '0']:  # check if the colorEditor dialog was canceled
            return
        raw_color = [float(i) for i in _color]
        raw_q_color = [round(float(i) * 255.0) for i in _color]
        cc_color = [round(float(i) * 255.0) for i in cmds.colorManagementConvert(toDisplaySpace=raw_color)]
        visual_name = QtGui.QColor(*cc_color).name()
        # print(cc_color)
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
            return pm.warning(ensure_text(text[self._L]))
        elif pm.objExists("Sine_" + self.line_edit.text() + "_MCtl") or pm.objExists("Sine_" + self.line_edit.text()):
            text = ["Name already exists!", "指定の名前はすでに存在しています"]
            return pm.warning(ensure_text(text[self._L]))
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

    def make_tooltips_toplayer(self):
        self.titleBar.minimize_button._tooltip.raise_()
        self.titleBar.maximize_restore_button._tooltip.raise_()
        self.titleBar.close_button._tooltip.raise_()


class ColorIndexGroup(QtWidgets.QWidget):
    btn_clicked = QtCore.Signal()

    def __init__(self):
        super(ColorIndexGroup, self).__init__()
        self.current_index = None
        self.current_cc_color = None

        self.color_index = COLOR_INDEX
        self.cc_color_index = {}

        main_layout = FlowLayout(self)
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
