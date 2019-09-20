# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.Qt import QLabel, QListView, QLineEdit, QFormLayout, QHBoxLayout, \
    QPushButton, QVBoxLayout, QWidget, QMessageBox

from scripts import Utils


class ChannelListWidget(QWidget):
    def __init__(self, main, channels):
        super(ChannelListWidget, self).__init__()
        self.main_win = main
        self.channels = channels
        self.channel_index = len(channels)-1
        self.linedit_list = []
        self.sdks = []
        for channel in self.channels:
            self.sdks.append(channel['channelId'])
        self.sdks.append(" + 添加渠道")

        self.setObjectName("ChannelListWidget")

        v_layout1 = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        list_model = QStringListModel()
        list_model.setStringList(self.sdks)
        self.channel_list_view = QListView()
        self.channel_list_view.setModel(list_model)
        self.channel_list_view.clicked.connect(self.list_item_onclick)
        h_layout1.addWidget(self.channel_list_view, 1)

        self.channel = self.channels[self.channel_index]

        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 100, 10, 50)
        form_layout.addRow("游戏ID：", QLabel(self.main_win.games[self.main_win.game_index]['id']))
        form_layout.addRow("渠道ID：", QLabel(self.channel['channelId']))
        self.game_name_value = QLineEdit()
        form_layout.addRow("游戏名称：", self.game_name_value)
        self.game_package_value = QLineEdit()
        form_layout.addRow("游戏包名：", self.game_package_value)
        self.game_vcode_value = QLineEdit()
        form_layout.addRow("游戏版本号：", self.game_vcode_value)
        self.game_vname_value = QLineEdit()
        form_layout.addRow("游戏版本名：", self.game_vname_value)
        self.debug_value = QLineEdit()
        form_layout.addRow("打印日志：", self.debug_value)
        h_layout1.addLayout(form_layout, 4)

        self.form_layout2 = QFormLayout()
        self.form_layout2.setContentsMargins(10, 100, 10, 50)
        self.set_info()
        h_layout1.addLayout(self.form_layout2, 4)
        v_layout1.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        back_btn = QPushButton("返 回")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back)
        h_layout2.addWidget(back_btn, alignment=Qt.AlignLeft | Qt.AlignBottom)

        save_btn = QPushButton("保 存")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self.save_data)
        h_layout2.addWidget(save_btn, alignment=Qt.AlignHCenter)

        pack_btn = QPushButton("打 包")
        pack_btn.setFixedWidth(100)
        pack_btn.clicked.connect(self.to_package)
        h_layout2.addWidget(pack_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        v_layout1.addLayout(h_layout2)
        self.setLayout(v_layout1)

    def set_info(self):
        self.game_name_value.setText(self.channel['gameName'])
        self.game_package_value.setText(self.channel['package'])
        self.game_vcode_value.setText(self.channel['gameVersionCode'])
        self.game_vname_value.setText(self.channel['gameVersionName'])
        self.debug_value.setText(self.channel['debug'])
        # 先清空表单 （因为formlayout清除一行，会自动上移，所以只需remove第一行）
        i = 0
        row_count = self.form_layout2.rowCount()
        while i < row_count:
            self.form_layout2.removeRow(0)
            i += 1
        self.linedit_list.clear()
        # 再添加当前选择的渠道参数
        channel_name = QLabel(self.channel['name'] + '\t\t\tVersion:' + self.channel['sdkVersionName'] + '\t\tUpdate:' + self.channel['sdkUpdateTime'])
        channel_name.setAlignment(Qt.AlignRight)
        self.form_layout2.addRow(channel_name)
        for param in self.channel['sdkParams']:
            line_edit = QLineEdit(param['value'])
            self.form_layout2.addRow(param['showName'] + '：', line_edit)
            self.linedit_list.append(line_edit)

    def list_item_onclick(self):
        if self.channel_list_view.currentIndex().row() == len(self.sdks)-1:
            self.main_win.set_add_channel_widget(self.channels)
        else:
            self.channel_index = self.channel_list_view.currentIndex().row()
            self.channel = self.channels[self.channel_index]
            self.set_info()

    def back(self):
        self.main_win.set_game_list_widget(self.main_win.games)

    def to_package(self):
        if not self.save_data():
            return
        self.main_win.set_package_widget(self.channels)

    def save_data(self):
        self.channel['gameName'] = self.game_name_value.text().strip()
        self.channel['package'] = self.game_package_value.text().strip()
        self.channel['gameVersionCode'] = self.game_vcode_value.text().strip()
        self.channel['gameVersionName'] = self.game_vname_value.text().strip()
        self.channel['debug'] = self.debug_value.text().strip()
        i = 0
        while i < len(self.linedit_list):
            if self.linedit_list[i].text().strip() == "":
                QMessageBox.warning(self, "警告", "渠道参数不能为空！")
                return False
            self.channel['sdkParams'][i]['value'] = self.linedit_list[i].text().strip()
            i += 1
        self.channels[self.channel_index] = self.channel
        game_id = self.main_win.games[self.main_win.game_index]['id']
        Utils.update_channels(Utils.get_full_path('games/' + game_id + '/config.xml'), self.channel, self.channel_index)
        return True
