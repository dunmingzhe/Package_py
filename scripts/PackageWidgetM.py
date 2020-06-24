# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt, QSize, QStringListModel
from PyQt5.Qt import QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QListView, QListWidget, QProgressDialog,\
    QWidget, QToolBox, QScrollArea, QProgressBar, QFileDialog, QMessageBox, QListWidgetItem, QAbstractItemView

from scripts import Utils
from scripts.PackTask import PackageMonitor, PackRunnable


class PackageWidgetM(QWidget):
    def __init__(self, main):
        super(PackageWidgetM, self).__init__()
        self.setObjectName("PackageWidgetM")
        self.main_win = main
        self.game_index = 0
        self.selected = []  # 已选中的channel及所属game列表 如：[{"game": 当前game字典, "channel": 当前channel字典}, {}, {}]
        self.selected_name = []  # 已选中的渠道显示名称列表 如：["10878922-765321", "", "", ""]
        self.lbps = {}  # 打包信息及进度条组合字典 {"765321": {}, "": {}}
        self.progress = None
        self.monitor = PackageMonitor()
        self.monitor.signal.connect(self.complete)

        v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        # 全部游戏及其下的渠道列表
        self.tool_box = QToolBox(self)
        self.tool_box.setFixedWidth(100)
        for game in self.main_win.games:
            clv = QListView()
            clv.setEditTriggers(QAbstractItemView.NoEditTriggers)
            clv.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tool_box.addItem(clv, game['id'])
        self.tool_box.currentChanged.connect(self.select_game)
        self.tool_box.setCurrentIndex(self.game_index)
        channel_list_area = QScrollArea()
        channel_list_area.setWidget(self.tool_box)
        h_layout1.addWidget(channel_list_area, 1)
        # 已选择的渠道列表
        self.cslv_model = QStringListModel()
        self.cslv_model.setStringList([])
        self.cslv = QListView()
        self.cslv.setModel(self.cslv_model)
        self.cslv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cslv.doubleClicked.connect(self.delete_channel)
        self.cslv.setContextMenuPolicy(Qt.CustomContextMenu)
        h_layout1.addWidget(self.cslv, 2)
        # 打包进度条显示列表
        self.qpb_list_widget = QListWidget()
        self.qpb_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.qpb_list_widget.itemDoubleClicked.connect(self.select_qpb_list)
        h_layout1.addWidget(self.qpb_list_widget, 5)
        v_layout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        self.back_btn = QPushButton("返 回")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.back)
        h_layout2.addWidget(self.back_btn, alignment=Qt.AlignLeft | Qt.AlignBottom)

        h_layout2.addSpacing(100)
        select_apk_btn = QPushButton("选择母包:")
        select_apk_btn.setFixedWidth(100)
        select_apk_btn.clicked.connect(self.select_apk)
        h_layout2.addWidget(select_apk_btn)
        self.apk_path = QLabel()
        self.apk_path.setText("<h3><font color=%s>%s</font></h3>" % ('red', "请浏览选择本地母包路径"))
        h_layout2.addWidget(self.apk_path)
        h_layout2.addSpacing(100)

        self.pack_btn = QPushButton("打 包")
        self.pack_btn.setFixedWidth(100)
        self.pack_btn.clicked.connect(self.click)
        h_layout2.addWidget(self.pack_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        v_layout.addLayout(h_layout2)
        self.setLayout(v_layout)

    def select_game(self, p_int):
        self.game_index = p_int
        if 'apk' in self.main_win.games[self.game_index]:
            self.apk_path.setText(self.main_win.games[self.game_index]['apk'])
        else:
            self.apk_path.setText("<h3><font color=%s>%s</font></h3>" % ('red', "请浏览选择本地母包路径"))
            # self.apk_path.setText("请浏览选择本地母包路径")
        # 当前选中的game,其下的所有渠道列表
        self.channels = Utils.get_channels(Utils.get_full_path('games/' + self.main_win.games[p_int]['id'] + '/config.xml'))
        channel_ids = []
        for channel in self.channels:
            channel_ids.append(channel['channelId'])
        list_model = QStringListModel()
        list_model.setStringList(channel_ids)
        self.clv = self.tool_box.currentWidget()
        self.clv.doubleClicked.connect(self.select_channel)
        self.clv.setModel(list_model)

    # 双击选中当前渠道，更新已选中列表的model
    def select_channel(self):
        if 'apk' not in self.main_win.games[self.game_index]:
            QMessageBox.warning(self, "警告", "请先添加母包！")
            return
        channel = self.channels[self.clv.currentIndex().row()]
        name = self.main_win.games[self.game_index]['id'] + '-' + channel['channelId']
        if name in self.selected_name:
            return
        self.selected_name.append(name)
        self.cslv_model.setStringList(self.selected_name)
        package = {'game': self.main_win.games[self.game_index], 'channel': channel}
        self.selected.append(package)

    # 双击移除当前渠道，更新已选中列表的model
    def delete_channel(self):
        name = self.selected_name[self.cslv.currentIndex().row()]
        self.selected_name.remove(name)
        self.cslv_model.setStringList(self.selected_name)
        package = self.selected[self.cslv.currentIndex().row()]
        self.selected.remove(package)

    def select_qpb_list(self):
        index = self.qpb_list_widget.currentIndex().row()
        game_id = self.selected[index]['game']['id']
        channel_id = self.selected[index]['channel']['channelId']
        success = self.lbps[channel_id]['success']
        dest_apk_dir = Utils.get_full_path('output/' + game_id + '/' + channel_id)
        if success:
            os.startfile(dest_apk_dir)
        else:
            QMessageBox.warning(self, "警告", "打包成功了吗？")

    def back(self):
        self.monitor.deleteLater()
        self.main_win.set_main_widget()

    def select_apk(self):
        f_name = QFileDialog.getOpenFileName(self, '选择母包', os.path.join(os.path.expanduser('~'), "Desktop"), ("Apk (*.apk)"))
        if f_name[0]:
            self.apk_path.setStyleSheet("font-size:12px")
            self.apk_path.setText(f_name[0])
            self.main_win.games[self.game_index]['apk'] = f_name[0]

    def click(self):
        if self.pack_btn.text() == "打 包":
            self.package()
        elif self.pack_btn.text() == "取 消":
            self.cancel()

    def package(self):
        # 清空上次打包完成后的进度条显示列表
        count = self.qpb_list_widget.count()
        if count > 0:
            for i in range(count):
                item = self.qpb_list_widget.takeItem(0)
                del item

        if len(self.selected) <= 0:
            QMessageBox.warning(self, "警告", "请选择需要打包的渠道！")
            return
        for package in self.selected:
            # {"success": 是否成功, "label": 进度条文本view, "qpb": 进度条view, "runnable": 打包任务}
            lbp = {'success': False}
            self.set_qpb_list_item(package['channel']['channelId'], lbp)
            runnable = PackRunnable(package['game'], package['channel'], package['game']['apk'])
            runnable.signal.signal.connect(self.set_value)
            self.monitor.add_runnable(runnable)
            lbp['runnable'] = runnable
            self.lbps[package['channel']['channelId']] = lbp
        # 开启监听线程
        self.monitor.start()
        # 开始打包，不可返回，返回按钮禁用；设置打包按钮文本为"取 消"
        self.back_btn.setDisabled(True)
        self.pack_btn.setText("取 消")

    def set_qpb_list_item(self, channel_id, lbp):
        item = QListWidgetItem(self.qpb_list_widget)
        item.setSizeHint(QSize(400, 80))
        widget = QWidget(self.qpb_list_widget)
        v_layout = QVBoxLayout()
        label = QLabel(channel_id + "==>>>等待出包...")
        v_layout.addWidget(label)
        lbp['label'] = label
        qpb = QProgressBar(self.qpb_list_widget)
        v_layout.addWidget(qpb)
        lbp['qpb'] = qpb
        widget.setLayout(v_layout)
        self.qpb_list_widget.addItem(item)
        self.qpb_list_widget.setItemWidget(item, widget)

    def set_value(self, channel_id, result, msg, step):
        lbp = self.lbps[channel_id]
        if result:  # 打包步骤异常，提示异常，关闭进度条
            lbp['label'].setText(channel_id + "==>>>" + msg)
            lbp['qpb'].close()
            if step == 100:
                lbp['success'] = True
                self.lbps[channel_id] = lbp
        else:   # 打包正常，设置进度条进度
            lbp['qpb'].setValue(step)
            if step == 0:
                lbp['label'].setText(channel_id + "==>>>" + msg)

    # 取消打包（全部取消）
    def cancel(self):
        self.progress = QProgressDialog(self)
        self.progress.setFixedWidth(500)
        self.progress.setFixedHeight(80)
        self.progress.setWindowTitle("正在取消，请稍等...")
        self.progress.setCancelButtonText("取消")
        self.progress.setMinimumDuration(1)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setRange(0, 0)
        self.progress.show()
        # 清空进度条显示列表
        count = self.qpb_list_widget.count()
        for i in range(count):
            item = self.qpb_list_widget.takeItem(0)
            del item

        # 清空任务线程池；线程池清空后，会触发监听线程的完成信号，重置返回和打包按钮
        # 因为打包任务调用外部程序，并不能立即终止外部程序连接，所以清空过程有延迟
        for channel_id in self.lbps:
            self.lbps[channel_id]['runnable'].is_close = True
        self.monitor.clear()

    # 取消打包（清空任务完成），或打包完成，
    def complete(self):
        if self.progress is not None:
            self.progress.cancel()
        # 返回按钮解禁；设置打包按钮文本为"打 包"
        self.back_btn.setDisabled(False)
        self.pack_btn.setText("打 包")
