# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt, QSize, QThreadPool
from PyQt5.Qt import QLabel, QLineEdit, QHBoxLayout, QPushButton, QVBoxLayout, QListWidget,\
    QWidget, QScrollArea, QCheckBox, QProgressBar, QFileDialog, QMessageBox, QListWidgetItem

from scripts.PackRunnable import PackRunnable


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

        v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        # self.cbox_list_widget = QListWidget()
        # item = QListWidgetItem(self.cbox_list_widget)
        # self.all_seleced_cbox = QCheckBox("全  选")
        # self.all_seleced_cbox.stateChanged.connect(self.select_all)
        # self.cbox_list_widget.setItemWidget(item, self.all_seleced_cbox)
        # for channel in self.channels:
        #     item = QListWidgetItem(self.cbox_list_widget)
        #     cbox = QCheckBox(channel['channelId'])
        #     self.cbox_list_widget.setItemWidget(item, cbox)
        # h_layout1.addWidget(self.cbox_list_widget, 1)
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
        back_btn = QPushButton("返 回")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back)
        h_layout2.addWidget(back_btn, alignment=Qt.AlignLeft | Qt.AlignBottom)

        h_layout2.addSpacing(100)
        select_apk_btn = QPushButton("选择母包:")
        select_apk_btn.clicked.connect(self.select_apk)
        h_layout2.addWidget(select_apk_btn)
        self.apk_path = QLineEdit()
        self.apk_path.setPlaceholderText("母包路径")
        h_layout2.addWidget(self.apk_path)
        h_layout2.addSpacing(100)

        pack_btn = QPushButton("打 包")
        pack_btn.setFixedWidth(100)
        pack_btn.clicked.connect(self.package)
        h_layout2.addWidget(pack_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        v_layout.addLayout(h_layout2)
        self.setLayout(v_layout)

    def back(self):
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

    def package(self):
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
            channel = self.channels[i]
            item = QListWidgetItem(self.qpb_list_widget)
            item.setSizeHint(QSize(400, 80))
            widget = QWidget(self.qpb_list_widget)
            v_layout = QVBoxLayout()
            h_layout = QHBoxLayout()
            label = QLabel(channel['channelId'] + " 正在出包...")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            h_layout.addWidget(label)
            lbp['label'] = label
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(lambda: self.cancel(i))
            h_layout.addWidget(cancel_btn, alignment=Qt.AlignRight)
            lbp['btn'] = cancel_btn
            v_layout.addLayout(h_layout)
            qpb = QProgressBar(self.qpb_list_widget)
            v_layout.addWidget(qpb)
            lbp['qpb'] = qpb
            widget.setLayout(v_layout)
            self.qpb_list_widget.addItem(item)
            self.qpb_list_widget.setItemWidget(item, widget)
            self.lbps[channel['channelId']] = lbp
            runnable = PackRunnable(game, channel, apk)
            runnable.signal.signal.connect(self.set_value)
            self.pool.start(runnable)

    def set_value(self, channel_id, result, msg, step):
        lbp = self.lbps[channel_id]
        if result:
            lbp['label'].setText(channel_id + " 出包失败：" + msg)
            lbp['qpb'].close()
        else:
            lbp['qpb'].setValue(step)
            if step == 100:
                lbp['label'].setText(channel_id + " 出包成功：" + msg)
                lbp['qpb'].close()

    def cancel(self, i):
        # TODO
        print(self.qpb_list_widget.currentIndex().row())
        print(i)
