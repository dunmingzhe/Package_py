# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.Qt import QLabel, QListView, QLineEdit, QFormLayout, QHBoxLayout, \
    QPushButton, QVBoxLayout, QWidget, QMessageBox, QMenu, QAction

from scripts import Utils


class ChannelListWidget(QWidget):
    def __init__(self, main, channels):
        super(ChannelListWidget, self).__init__()
        self.main_win = main
        self.channels = channels
        self.channel_index = len(channels)-1
        self.linedit_list = []
        self.channel_ids = []
        for channel in self.channels:
            self.channel_ids.append(channel['channelId'])
        self.channel_ids.append(" + 添加渠道")

        self.setObjectName("ChannelListWidget")

        v_layout1 = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        self.list_model = QStringListModel()
        self.list_model.setStringList(self.channel_ids)
        self.channel_list_view = QListView()
        self.channel_list_view.setModel(self.list_model)
        self.channel_list_view.clicked.connect(self.list_item_onclick)
        self.channel_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channel_list_view.customContextMenuRequested.connect(self.show_del_menu)
        h_layout1.addWidget(self.channel_list_view, 1)

        self.channel = self.channels[self.channel_index]

        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 100, 10, 50)
        form_layout.addRow("游戏ID：", QLabel(self.main_win.games[self.main_win.game_index]['id']))
        self.channel_id_value = QLabel(self.channel['channelId'])
        self.channel_id_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        form_layout.addRow("渠道ID：", self.channel_id_value)
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
        self.channel_id_value.setText(self.channel['channelId'])
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
        if self.channel_list_view.currentIndex().row() == len(self.channel_ids)-1:
            self.main_win.set_add_channel_widget(self.channels, self.channel)
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
        print(self.channel)
        Utils.update_channels(Utils.get_full_path('games/' + game_id + '/config.xml'), self.channel, self.channel_index)
        return True

    def show_del_menu(self, point):
        self.list_item_onclick()
        if -1 < self.channel_index < len(self.channel_ids)-1:
            menu = QMenu(self.channel_list_view)
            del_action = QAction("删 除", menu)
            del_action.triggered.connect(self.del_channel)
            menu.addAction(del_action)
            menu.popup(self.channel_list_view.mapToGlobal(point))

    def del_channel(self):
        reply = QMessageBox.warning(self, "警告", "确定删除当前渠道？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 更新listview
            self.channel_ids.pop(self.channel_index)
            self.list_model.setStringList(self.channel_ids)
            # 更新表单view（index前移一位）
            self.channel = self.channels[self.channel_index-1]
            self.set_info()
            # 更新本地数据
            self.channels.pop(self.channel_index)
            game_id = self.main_win.games[self.main_win.game_index]['id']
            Utils.del_channel(Utils.get_full_path('games/' + game_id + '/config.xml'), self.channel_index)
            # 重置index，防止 index out of range
            self.channel_index = self.channel_index - 1
