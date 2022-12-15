import ast
from functools import partial

from maya import cmds

import pymel.core as pm

from ..ui.templates.main_window import MainWindow, SubWindow
from ..ui.templates.widgets import IntSliderGroup, FloatSliderGroup, FlowLayout
from ..ui.widgets.py_combobox import PyCombobox
from ..ui.widgets.py_list_widget import PyListWidget
from ..ui.widgets.py_push_button import PyPushButton
from .widgets.py_icon_button import PyIconButton
from .widgets.py_line_edit import PyLineEdit
from ..qt_core import *
from ..operation import SineSetupMain

_dir_name = os.path.dirname(__file__)
icon_dir = os.path.join(_dir_name, "images", "svg_icons")

_L = LANGUAGE = 0  # 0 for English, 1 for Japanese

COLOR_INDEX = {}
for __COLOR in range(2, 32):
    COLOR_INDEX[__COLOR] = [round(X * 255.0) for X in cmds.colorIndex(__COLOR, q=1)]


class SineUI(MainWindow):
    def __init__(self):
        super(SineUI, self).__init__()
        self.source_checker = []
        self.settings_dialog = SineSettingsDialog()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        icon_path = os.path.join(icon_dir, "active_menu.svg")

    def create_widgets(self):
        font = QtGui.QFont()
        font.setPointSize(6 * DPI_SCALE)
        font.setBold(True)
        text = ["Tips:select name space", "ネームスペースを選択してください"]
        self.top_label = QtWidgets.QLabel(text[_L])
        self.top_label.setAlignment(QtCore.Qt.AlignCenter)
        self.top_label.setFont(font)
        self.top_label.setMargin(14 * DPI_SCALE)

        text = ["add Controller", "コントローラを追加"]
        self.left_top_btn = PyPushButton(text[_L])
        text = ["remove Controller", "コントローラを除去"]
        self.left_top_btn2 = PyPushButton(text[_L])
        text = ["Delete Selected", "選択を削除"]
        self.right_top_btn = PyPushButton(text[_L])

        self.name_spacing_cbx = PyCombobox()
        cmds.namespace(setNamespace=':')
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        namespaces = list((set(namespaces) - {'UI', 'shared'}))
        namespaces.insert(0, "-- root -- (no name space)")
        self.name_spacing_cbx.addItems(namespaces)

        self.source_lw = PyListWidget()
        self.source_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Create", "コントローラを作成"]
        self.left_btn = PyPushButton(text[_L])
        text = ["Create Exp", "エクスプレーションを作成"]
        self.left_btn2 = PyPushButton(text[_L])

        self.master_lw = PyListWidget()
        self.master_lw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        text = ["Delete All", "全て削除"]
        self.right_btn2 = PyPushButton(text[_L])

    def create_layout(self):

        # left
        left_layout = QtWidgets.QVBoxLayout()

        top_left_btn_layout = QtWidgets.QHBoxLayout()
        top_left_btn_layout.addWidget(self.left_top_btn)
        top_left_btn_layout.addWidget(self.left_top_btn2)

        source_list_layout = QtWidgets.QVBoxLayout()
        source_list_layout.addWidget(self.source_lw)

        left_btn_layout = QtWidgets.QHBoxLayout()
        left_btn_layout.addWidget(self.left_btn)
        left_btn_layout.addWidget(self.left_btn2)

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
        right_btn_layout.addWidget(self.right_btn2)

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

    def create_connections(self):
        self.left_top_btn.clicked.connect(self.add_source)
        self.left_top_btn2.clicked.connect(self.remove_source)
        self.left_btn.clicked.connect(self.add_master)
        self.left_btn2.clicked.connect(self.make_exp)

    def add_source(self):
        sl = pm.ls(os=1, o=1)
        if not sl:  # maybe add a condition to limit len(sl)>1 ?
            return
        if self.source_checker:
            for i in sl:
                if i in self.source_checker:
                    text = ["object '{}' already assigned".format(i),
                            "オブジェクト '{}' はすでに割り当てられています".format(i)]
                    return pm.warning()
        text = str([i.name() for i in sl])
        self.source_lw.addItem(text)
        [self.source_checker.append(i) for i in sl if i not in self.source_checker]

    def remove_source(self):
        if not self.source_lw.selectedIndexes():
            return
        indices = [(i.row(), i) for i in self.source_lw.selectedIndexes()]
        indices.sort(key=lambda i: i[0], reverse=True)
        for i in indices:
            items = ast.literal_eval(self.source_lw.itemFromIndex(i[1]).text())
            [self.source_checker.remove(i) for i in items if i in self.source_checker]
            self.source_lw.takeItem(i[0])

    def add_master(self):
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
                return pm.warning(text[_L])
            matrices[current_index] = [pm.xform(i, q=1, m=1, ws=1) for i in pynodes]

        self.settings_dialog.show()
        if self.settings_dialog.exec_() == QtWidgets.QDialog.Accepted:
            master = SineSetupMain(elements, matrices, self.settings_dialog.config)
            self.master_lw.addItem(master.config["name"])

    def make_exp(self):
        pass

    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)
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
        self.line_edit.setValidator(QtGui.QRegExpValidator("^[a-zA-Z][a-zA-Z0-9_]*$"))
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
            return pm.warning(text[_L])
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


"""
    def store_config_file(self):
        config_description = dict(skinPath=self.folder_path_le.text(),
                                  fileExt=self.export_format_cb.currentIndex(),
                                  useStoredList=self.obj_storage_chk.isChecked(),
                                  objList=self.obj_storage_le.text(),
                                  skip_already_skinned=self.skip_already_skinned_chk.isChecked(),
                                  )
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            pm.displayInfo("config folder created : {}".format(CONFIG_DIR))
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_description, f)
        debug("config stored : {}".format(config_description))

    def restore_config(self):
        if os.path.exists(CONFIG_FILE):
            f = open(CONFIG_FILE)
            config = json.load(f)
            debug("config loaded: {}".format(config))
            try:
                self.folder_path_le.setText(str(config["skinPath"]))
                self.export_format_cb.setCurrentIndex(config["fileExt"])
                self.obj_storage_chk.setChecked(config['useStoredList'])
                self.obj_storage_le.setText(str(config["objList"]))
                self.skin_table.update_model(config["skinPath"], self.export_format_cb.currentText())
                self.skip_already_skinned_chk.setChecked(config["skip_already_skinned"])
            except:
                pass
"""
