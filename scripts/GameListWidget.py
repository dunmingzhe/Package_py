# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.Qt import QLabel, QListView, QLineEdit, QFormLayout, QHBoxLayout, \
    QPushButton, QVBoxLayout, QTextEdit, QFileDialog, QMessageBox, QWidget, QAbstractItemView
from PyQt5.QtGui import QPixmap

from scripts import Utils
from scripts.GameListModel import GameListModel


class GameListWidget(QWidget):
    def __init__(self, main):
        super(GameListWidget, self).__init__()
        self.main_win = main
        self.keystore_exchanged = False

        self.setObjectName("GameListWidget")
        v_layout = QVBoxLayout()

        h_layout1 = QHBoxLayout()
        self.game_list_view = QListView()
        self.game_list_view.setViewMode(QListView.ListMode)
        self.game_list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.game_list_model = GameListModel(self.main_win.games)
        self.game_list_view.setModel(self.game_list_model)
        self.game_list_view.clicked.connect(self.list_item_onclick)
        h_layout1.addWidget(self.game_list_view, 1)

        self.game = self.main_win.games[self.main_win.game_index]

        form_layout = QFormLayout()
        form_layout.setContentsMargins(20, 50, 20, 50)
        self.game_name_value = QLineEdit()
        form_layout.addRow("游戏名称：", self.game_name_value)
        self.game_desc_value = QTextEdit()
        form_layout.addRow("游戏简介：", self.game_desc_value)
        self.game_appid_value = QLabel()
        self.game_appid_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        form_layout.addRow("游戏ID：", self.game_appid_value)
        self.game_appkey_value = QLabel()
        self.game_appkey_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        form_layout.addRow("客户端Key：", self.game_appkey_value)
        h_layout = QHBoxLayout()
        self.keystore_path = QLineEdit()
        select_key_btn = QPushButton("浏览")
        select_key_btn.setStyleSheet('QPushButton{border-radius: 0px;}')
        select_key_btn.clicked.connect(self.select_ketstore)
        h_layout.addWidget(self.keystore_path)
        h_layout.addWidget(select_key_btn)
        form_layout.addRow("KeyStore:", h_layout)
        self.keystore_pwd_value = QLineEdit()
        form_layout.addRow("KeyPass:", self.keystore_pwd_value)
        self.keystore_alias_value = QLineEdit()
        form_layout.addRow("Alias:", self.keystore_alias_value)
        self.keystore_aliaspwd_value = QLineEdit()
        form_layout.addRow("AliasPass:", self.keystore_aliaspwd_value)
        h_layout1.addLayout(form_layout, 3)

        v_layout1 = QVBoxLayout()
        v_layout1.addStretch(1)
        self.icon_img = QLabel()
        self.icon_img.setMaximumSize(QtCore.QSize(200, 200))
        self.icon_img.setMinimumSize(QtCore.QSize(200, 200))
        self.icon_img.setScaledContents(True)
        v_layout1.addWidget(self.icon_img)
        icon_exchange_btn = QPushButton("更换Icon")
        icon_exchange_btn.setFixedWidth(100)
        icon_exchange_btn.clicked.connect(self.exchange_icon)
        v_layout1.addWidget(icon_exchange_btn, alignment=Qt.AlignHCenter)
        v_layout1.addStretch(2)
        h_layout1.addLayout(v_layout1, 1)
        v_layout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()
        create_game_btn = QPushButton("返 回")
        create_game_btn.setFixedWidth(100)
        create_game_btn.clicked.connect(self.back)
        h_layout2.addWidget(create_game_btn, alignment=Qt.AlignLeft | Qt.AlignBottom)
        back_btn = QPushButton("创建游戏")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.add_game)
        h_layout2.addWidget(back_btn, alignment=Qt.AlignHCenter)
        next_btn = QPushButton("下一步")
        next_btn.setFixedWidth(100)
        next_btn.clicked.connect(self.next)
        h_layout2.addWidget(next_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        v_layout.addLayout(h_layout2)
        self.setLayout(v_layout)
        self.set_game_info()

    def set_game_info(self):
        self.game_name_value.setText(self.game['name'])
        self.game_desc_value.setText(self.game['desc'])
        self.game_appid_value.setText(self.game['id'])
        self.game_appkey_value.setText(self.game['key'])
        self.keystore_path.setText(self.game['keystore'])
        self.keystore_pwd_value.setText(self.game['keypwd'])
        self.keystore_alias_value.setText(self.game['alias'])
        self.keystore_aliaspwd_value.setText(self.game['aliaspwd'])

        icon = Utils.get_full_path('games/' + self.game['id'] + '/icon/icon.png')
        if not os.path.exists(icon):
            icon = 'icon.png'
        self.icon_img.setPixmap(QPixmap(icon))

    def list_item_onclick(self):
        self.main_win.game_index = self.game_list_view.currentIndex().row()
        self.game = self.main_win.games[self.main_win.game_index]
        self.set_game_info()

    def back(self):
        self.main_win.set_main_widget()

    def add_game(self):
        if not self.save_data():
            return
        self.main_win.set_create_game_widget(self.main_win.games)

    def select_ketstore(self):
        fname = QFileDialog.getOpenFileName(self, '选择签名文件', Utils.get_full_path('games/' + self.game['id'] + '/keystore/'))
        if fname[0]:
            if os.path.samefile(fname[0], Utils.get_full_path('games/' + self.game['id'] + '/keystore/' + self.game['keystore'])):
                self.keystore_path.setText(self.game['keystore'])
                self.keystore_pwd_value.setText(self.game['keypwd'])
                self.keystore_alias_value.setText(self.game['alias'])
                self.keystore_aliaspwd_value.setText(self.game['aliaspwd'])
                self.keystore_exchanged = False
            else:
                self.keystore_path.setText(fname[0])
                self.keystore_pwd_value.clear()
                self.keystore_alias_value.clear()
                self.keystore_aliaspwd_value.clear()
                self.keystore_exchanged = True

    def exchange_icon(self):
        fname = QFileDialog.getOpenFileName(self, '选择icon', Utils.get_full_path('games/' + self.game['id'] + '/icon/'), ("Images (*.png)"))
        if fname[0]:
            pix = QPixmap(fname[0])
            if pix.width() != 512 or pix.height() != 512:
                QMessageBox.warning(self, "警告", "必须上传512*512.png图片")
                return
            self.icon_img.setPixmap(pix)
            current_icon = Utils.get_full_path('games/' + self.game['id'] + '/icon/icon.png')
            if os.path.exists(current_icon):
                if os.path.samefile(os.path.dirname(fname[0]), os.path.dirname(current_icon)):
                    if not os.path.samefile(fname[0], current_icon):    # 如果选中的，在game的icon目录下，但不是当前icon，则进行重命名
                        count = 0
                        temp = 'icon0.png'
                        while os.path.exists(Utils.get_full_path('games/' + self.game['id'] + '/icon/' + temp)):
                            count += 1
                            temp = 'icon' + str(count) + '.png'
                        os.renames(current_icon, Utils.get_full_path('games/' + self.game['id'] + '/icon/' + temp))
                        os.renames(fname[0], current_icon)
                    else:   # 如果所选的是当前icon，不做处理
                        return
                else:   # 如果选中的不在game的icon目录下，则重命名当前icon，并将选中的icon复制到目录下作为当前icon
                    count = 0
                    temp = 'icon0.png'
                    while os.path.exists(Utils.get_full_path('games/' + self.game['id'] + '/icon/' + temp)):
                        count += 1
                        temp = 'icon' + str(count) + '.png'
                    os.renames(current_icon, Utils.get_full_path('games/' + self.game['id'] + '/icon/' + temp))
                    Utils.copy_file(fname[0], current_icon)
            else:
                Utils.copy_file(fname[0], current_icon)

    def save_data(self):
        if self.game_name_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "游戏名称不能为空！")
            return False
        if self.keystore_path.text().strip() == "":
            QMessageBox.warning(self, "警告", "必须上传keystore签名文件！")
            return False
        if self.keystore_pwd_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "keystore密码不能为空！")
            return False
        if self.keystore_alias_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "alias不能为空！")
            return False
        if self.keystore_aliaspwd_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "alias密码不能为空！")
            return False
        self.game['name'] = self.game_name_value.text().strip()
        self.game['desc'] = self.game_desc_value.toPlainText().strip()
        if self.keystore_exchanged:
            keystore = os.path.basename(self.keystore_path.text().strip())
            self.game['keystore'] = keystore
            self.game['keypwd'] = self.keystore_pwd_value.text().strip()
            self.game['alias'] = self.keystore_alias_value.text().strip()
            self.game['aliaspwd'] = self.keystore_aliaspwd_value.text().strip()
            keystore_path = Utils.get_full_path('games/' + self.game['id'] + '/keystore/' + keystore)
            if not os.path.exists(keystore_path):
                Utils.copy_file(self.keystore_path.text().strip(), keystore_path)

        self.main_win.games[self.main_win.game_index] = self.game
        self.game_list_model.update_item(self.main_win.game_index, self.game)
        return Utils.update_games(Utils.get_full_path('games/games.xml'), self.game, self.main_win.game_index)

    def next(self):
        if not self.save_data():
            return
        channels = Utils.get_channels(Utils.get_full_path('games/' + self.game['id'] + '/config.xml'))
        if channels is None:
            if not os.path.exists(Utils.get_full_path('channelsdk')):
                QMessageBox.warning(self, "警告", os.path.dirname(os.getcwd()) + " 没有channelsdk文件夹")
                return
            elif len(os.listdir(Utils.get_full_path('channelsdk'))) <= 0:
                QMessageBox.warning(self, "警告", "本地没有渠道sdk，请手动添加sdk文件夹到" + Utils.get_full_path('channelsdk'))
                return
            channels = []
            self.main_win.set_add_channel_widget(channels)
        else:
            self.main_win.set_channel_list_widget(channels)
