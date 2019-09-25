# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt
from PyQt5.Qt import QHBoxLayout, QFormLayout, QLineEdit, QPushButton, \
    QVBoxLayout, QMessageBox, QWidget, QComboBox, QLabel

from scripts import Utils


class ChannelAddWidget(QWidget):

    def __init__(self, main, channels, default_channel=None):
        super(ChannelAddWidget, self).__init__()
        self.setObjectName("ChannelAddWidget")
        self.main_win = main
        self.channels = channels
        self.default_channel = default_channel
        self.channel = {}
        self.linedit_list = []
        self.game = self.main_win.games[self.main_win.game_index]
        combox_items = os.listdir(Utils.get_full_path('channelsdk'))

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
        game_appid_value = QLabel(self.game['id'])
        form_layout1.addRow("游戏ID：", game_appid_value)
        game_appid_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.channel_id_value = QLineEdit()
        self.channel_id_value.setPlaceholderText("必填参数")
        form_layout1.addRow("渠道ID：", self.channel_id_value)
        self.game_name_value = QLineEdit()
        self.game_name_value.setText(self.game['name'])
        form_layout1.addRow("游戏名称：", self.game_name_value)
        self.game_package_value = QLineEdit()
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
        # 默认松鼠SDK
        select_channel_combox.setCurrentText("songshu")
        self.select_channel("songshu")

    def select_channel(self, text):
        # 先初始化数据
        self.linedit_list.clear()
        self.channel.clear()
        # 排序包体参数，防止参数写入乱排序
        self.channel['name'] = ''
        self.channel['sdk'] = text
        self.channel['channelId'] = ''
        self.channel['gameName'] = ''
        self.channel['package'] = ''
        self.channel['gameVersionCode'] = ''
        self.channel['gameVersionName'] = ''
        self.channel['debug'] = "false"
        # 获取渠道参数定义
        if not Utils.get_channel_config(self.channel):
            return

        # 再添加当前选择的渠道参数模板，刷新界面（先清空之前渠道参数表单，再添加）
        for i in range(self.form_layout2.rowCount()):
            # 因为formlayout清除一行，会自动上移，所以只需remove第一行
            self.form_layout2.removeRow(0)
        channel_name = QLabel(self.channel['name'] + '\t\t\tVersion:' + self.channel['sdkVersionName']
                              + '\t\tUpdate:' + self.channel['sdkUpdateTime'])
        channel_name.setAlignment(Qt.AlignRight)
        self.form_layout2.addRow(channel_name)
        if self.default_channel is not None and text == self.default_channel['sdk']:
            self.channel_id_value.setText(self.default_channel['channelId'])
            self.game_name_value.setText(self.default_channel['gameName'])
            self.game_package_value.setText(self.default_channel['package'])
            self.game_vcode_value.setText(self.default_channel['gameVersionCode'])
            self.game_vname_value.setText(self.default_channel['gameVersionName'])
            for param in self.default_channel['sdkParams']:
                line_edit = QLineEdit()
                line_edit.setText(param['value'])
                self.form_layout2.addRow(param['showName'] + ':', line_edit)
                self.linedit_list.append(line_edit)
        else:
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
        for channel in self.channels:
            if self.channel['channelId'] == channel['channelId']:
                QMessageBox.warning(self, "警告", "渠道已存在！")
                return
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
        self.channels.append(self.channel)
        Utils.add_channel(Utils.get_full_path('games/' + self.game['id'] + '/config.xml'), self.channel)
        self.main_win.set_channel_list_widget(self.channels)
