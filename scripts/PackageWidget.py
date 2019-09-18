# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt, QSize, QThreadPool
from PyQt5.Qt import QLabel, QLineEdit, QHBoxLayout, QPushButton, QVBoxLayout, QListWidget,\
    QWidget, QScrollArea, QCheckBox, QProgressBar, QFileDialog, QMessageBox, QListWidgetItem

from scripts.PackRunnable import PackRunnable
from scripts.PackageMonitor import PackageMonitor


class PackageWidget(QWidget):
    def __init__(self, main, channels):
        super(PackageWidget, self).__init__()
        self.main_win = main
        self.channels = channels
        self.check_boxs = []
        self.lbps = {}
        self.setObjectName("PackageWidget")
        self.pool = QThreadPool()
        self.pool.globalInstance()
        self.pool.setMaxThreadCount(3)
        self.monitor = PackageMonitor(self.pool)
        self.monitor.signal.connect(self.complete)

        v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        cbox_widget = QWidget()
        v_layout1 = QVBoxLayout()
        self.all_selected_cbox = QCheckBox("全  选")
        self.all_selected_cbox.stateChanged.connect(self.select_all)
        v_layout1.addWidget(self.all_selected_cbox)
        for channel in self.channels:
            check_box = QCheckBox(channel['channelId'])
            check_box.setFixedWidth(100)
            v_layout1.addSpacing(10)
            v_layout1.addWidget(check_box)
            self.check_boxs.append(check_box)
        cbox_widget.setLayout(v_layout1)
        channel_list_area = QScrollArea()
        channel_list_area.setWidget(cbox_widget)
        h_layout1.addWidget(channel_list_area, 1)

        self.qpb_list_widget = QListWidget()
        h_layout1.addWidget(self.qpb_list_widget, 5)
        v_layout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        self.back_btn = QPushButton("返 回")
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.back)
        h_layout2.addWidget(self.back_btn, alignment=Qt.AlignLeft | Qt.AlignBottom)

        h_layout2.addSpacing(100)
        select_apk_btn = QPushButton("选择母包:")
        select_apk_btn.clicked.connect(self.select_apk)
        h_layout2.addWidget(select_apk_btn)
        self.apk_path = QLineEdit()
        self.apk_path.setPlaceholderText("母包路径")
        h_layout2.addWidget(self.apk_path)
        h_layout2.addSpacing(100)

        self.pack_btn = QPushButton("打 包")
        self.pack_btn.setFixedWidth(100)
        self.pack_btn.clicked.connect(self.click)
        h_layout2.addWidget(self.pack_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        v_layout.addLayout(h_layout2)
        self.setLayout(v_layout)

    def back(self):
        self.monitor.deleteLater()
        self.main_win.set_channel_list_widget(self.channels)

    def select_apk(self):
        fname = QFileDialog.getOpenFileName(self, '选择母包', os.path.join(os.path.expanduser('~'), "Desktop"), ("Apk (*.apk)"))
        if fname[0]:
            self.apk_path.setStyleSheet("font-size:12px")
            self.apk_path.setText(fname[0])

    def select_all(self):
        if self.all_selected_cbox.isChecked():
            for cbox in self.check_boxs:
                cbox.setChecked(True)
        else:
            for cbox in self.check_boxs:
                cbox.setChecked(False)

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

        indexs = []
        for i in range(len(self.channels)):
            if self.check_boxs[i].isChecked():
                indexs.append(i)
        if len(indexs) <= 0:
            QMessageBox.warning(self, "警告", "请选择需要打包的渠道！")
            return

        if self.apk_path.text().strip() == "":
            QMessageBox.warning(self, "警告", "母包未上传！")
            return

        game = self.main_win.games[self.main_win.game_index]
        apk = self.apk_path.text().strip().replace('\\', '/')
        for i in indexs:
            lbp = {}
            self.set_qpb_list_item(self.channels[i], lbp)
            runnable = PackRunnable(game, self.channels[i], apk)
            runnable.signal.signal.connect(self.set_value)
            self.pool.start(runnable)
            lbp['runnable'] = runnable
            self.lbps[self.channels[i]['channelId']] = lbp
        # 开启监听线程
        self.monitor.start()
        # 开始打包，不可返回，返回按钮禁用；设置打包按钮文本为"取 消"
        self.back_btn.setDisabled(True)
        self.pack_btn.setText("取 消")

    def set_qpb_list_item(self, channel, lbp):
        item = QListWidgetItem(self.qpb_list_widget)
        item.setSizeHint(QSize(400, 80))
        widget = QWidget(self.qpb_list_widget)
        v_layout = QVBoxLayout()
        label = QLabel(channel['channelId'] + "==>>>等待出包...")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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
        # 打包步骤异常，提示异常，关闭进度条
        if result:
            lbp['label'].setText(channel_id + "==>>>" + msg)
            if step != 0:
                lbp['qpb'].close()
        # 打包正常，设置进度条进度
        else:
            lbp['qpb'].setValue(step)

    # 取消打包（全部取消）
    def cancel(self):
        # 清空进度条显示列表
        count = self.qpb_list_widget.count()
        for i in range(count):
            item = self.qpb_list_widget.takeItem(0)
            del item

        # 清空任务线程池；线程池清空后，会触发监听线程的完成信号，重置返回和打包按钮
        # 因为打包任务调用外部程序，并不能立即终止外部程序连接，所以清空过程有延迟
        for channel_id in self.lbps:
            self.lbps[channel_id]['runnable'].is_close = True
        self.pool.clear()

    def complete(self):
        # 取消打包，或打包完成，清空复选框的选择
        self.all_selected_cbox.setChecked(False)
        for cbox in self.check_boxs:
            cbox.setChecked(False)
        # 取消打包，或打包完成，返回按钮解禁；设置打包按钮文本为"打 包"
        self.back_btn.setDisabled(False)
        self.pack_btn.setText("打 包")
