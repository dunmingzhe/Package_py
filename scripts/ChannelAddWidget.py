# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt
from PyQt5.Qt import QHBoxLayout, QFormLayout, QLineEdit, QPushButton, \
    QVBoxLayout, QMessageBox, QWidget, QComboBox, QLabel

from scripts import Utils


class ChannelAddWidget(QWidget):

    def __init__(self, main, channels):
        super(ChannelAddWidget, self).__init__()
        self.main_win = main
        self.channels = channels
        self.channel = {}
        self.linedit_list = []
        self.game = self.main_win.games[self.main_win.game_index]
        combox_items = os.listdir(Utils.get_full_path('channelsdk'))

        self.setObjectName("ChannelAddWidget")
        v_layout = QVBoxLayout()
        v_layout.addSpacing(30)
        select_channel_combox = QComboBox()
        select_channel_combox.addItems(combox_items)
        select_channel_combox.activated[str].connect(self.select_channel)
        v_layout.addWidget(select_channel_combox, alignment=Qt.AlignHCenter)
        v_layout.addSpacing(30)

        h_layout1 = QHBoxLayout()
        form_layout1 = QFormLayout()
        form_layout1.setContentsMargins(10, 10, 10, 0)
        form_layout1.addRow("游戏ID：", QLabel(self.game['id']))
        self.channel_id_value = QLineEdit()
        self.channel_id_value.setPlaceholderText("必填参数")
        form_layout1.addRow("渠道ID：", self.channel_id_value)
        self.game_name_value = QLineEdit()
        form_layout1.addRow("游戏名称：", self.game_name_value)
        self.game_package_value = QLineEdit()
        self.game_name_value.setText(self.game['name'])
        form_layout1.addRow("游戏包名：", self.game_package_value)
        self.game_vcode_value = QLineEdit()
        form_layout1.addRow("游戏版本号：", self.game_vcode_value)
        self.game_vname_value = QLineEdit()
        form_layout1.addRow("游戏版本名：", self.game_vname_value)
        self.debug_value = QLineEdit("false")
        form_layout1.addRow("打印日志：", self.debug_value)
        h_layout1.addLayout(form_layout1)
        self.form_layout2 = QFormLayout()
        self.form_layout2.setContentsMargins(10, 10, 10, 0)
        self.select_channel(combox_items[0])
        h_layout1.addLayout(self.form_layout2)
        v_layout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        back_btn = QPushButton("返 回")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back)
        h_layout2.addWidget(back_btn, alignment=Qt.AlignLeft)
        add_btn = QPushButton("添 加")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self.add)
        h_layout2.addWidget(add_btn, alignment=Qt.AlignRight)
        v_layout.addSpacing(50)
        v_layout.addLayout(h_layout2)

        self.setLayout(v_layout)

    def select_channel(self, text):
        # 先清空表单 （因为formlayout清除一行，会自动上移，所以只需remove第一行）
        i = 0
        row_count = self.form_layout2.rowCount()
        while i < row_count:
            self.form_layout2.removeRow(0)
            i += 1
        self.linedit_list.clear()
        # 先排序包体参数，防止参数写入乱排序
        self.channel['name'] = ''
        self.channel['sdk'] = text
        self.channel['channelId'] = ''
        self.channel['gameName'] = ''
        self.channel['package'] = ''
        self.channel['gameVersionCode'] = ''
        self.channel['gameVersionName'] = ''
        self.channel['debug'] = self.debug_value.text().strip()
        # 获取渠道参数定义
        Utils.get_channel_config(self.channel)
        # 再添加当前选择的渠道参数
        channel_name = QLabel(self.channel['name'] + '\t\t\tVersion:' + self.channel['sdkVersionName'] + '\t\tUpdate:' + self.channel['sdkUpdateTime'])
        channel_name.setAlignment(Qt.AlignRight)
        self.form_layout2.addRow(channel_name)
        for param in self.channel['sdkParams']:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("渠道参数必填")
            self.form_layout2.addRow(param['showName'] + ':', line_edit)
            self.linedit_list.append(line_edit)

    def back(self):
        if len(self.channels) <= 0:
            self.main_win.set_game_list_widget(self.main_win.games)
        else:
            self.main_win.set_channel_list_widget(self.channels)

    def add(self):
        if self.channel_id_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "渠道ID不能为空！")
            return
        self.channel['channelId'] = self.channel_id_value.text().strip()
        self.channel['gameName'] = self.game_name_value.text().strip()
        self.channel['package'] = self.game_package_value.text().strip()
        self.channel['gameVersionCode'] = self.game_vcode_value.text().strip()
        self.channel['gameVersionName'] = self.game_vname_value.text().strip()
        self.channel['debug'] = self.debug_value.text().strip()
        for i in range(len(self.linedit_list)):
            if self.linedit_list[i].text().strip() == "":
                QMessageBox.warning(self, "警告", "渠道参数不能为空！")
                return
            self.channel['sdkParams'][i]['value'] = self.linedit_list[i].text().strip()
        print(self.channel)
        self.channels.append(self.channel)
        Utils.add_channel(Utils.get_full_path('games/' + self.game['id'] + '/config.xml'), self.channel)
        self.main_win.set_channel_list_widget(self.channels)
