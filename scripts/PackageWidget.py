# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt
from PyQt5.Qt import QLineEdit, QHBoxLayout, QPushButton, QVBoxLayout,\
    QWidget, QScrollArea, QCheckBox, QProgressBar, QFileDialog, QMessageBox


class PackageWidget(QWidget):
    def __init__(self, main, channels):
        super(PackageWidget, self).__init__()
        self.main_win = main
        self.channels = channels
        self.check_boxs = []
        self.qpbs = []
        self.setObjectName("PackageWidget")

        v_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        cbox_widget = QWidget()
        v_layout1 = QVBoxLayout(cbox_widget)
        for channel in self.channels:
            check_box = QCheckBox(channel['channelId'])
            v_layout1.addWidget(check_box)
            self.check_boxs.append(check_box)
        cbox_widget.setLayout(v_layout1)
        channel_list_area = QScrollArea()
        channel_list_area.setWidget(cbox_widget)
        h_layout1.addWidget(channel_list_area, 1)

        qpb_widget = QWidget()
        qpb_widget.setMinimumSize(600, 480)
        v_layout2 = QVBoxLayout(qpb_widget)
        for channel in self.channels:
            qpb = QProgressBar()
            v_layout2.addWidget(qpb)
            self.qpbs.append(qpb)
        channel_qpb_area = QScrollArea()
        channel_qpb_area.setWidget(qpb_widget)
        h_layout1.addWidget(channel_qpb_area, 5)
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

    def package(self):
        indexs = []
        for i in range(len(self.check_boxs)):
            if self.check_boxs[i].checkState() == Qt.Checked:
                indexs.append(i)

        if len(indexs) <= 0:
            QMessageBox.warning(self, "警告", "请选择需要打包的渠道！")
            return

        if self.apk_path.text().strip() == "":
            QMessageBox.warning(self, "警告", "母包未上传！")
            return
        for i in indexs:
            self.qpbs[i].setValue(0)
            apk_path = self.apk_path.text().strip().replace('\\', '/')
            channle = self.channels[i]
