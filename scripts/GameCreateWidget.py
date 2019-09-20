# -*- coding: utf-8 -*-
import os

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.Qt import QLabel, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton, \
    QVBoxLayout, QFileDialog, QMessageBox, QWidget

from scripts import Utils


class GameCreateWidget(QWidget):

    def __init__(self, main):
        super(GameCreateWidget, self).__init__()
        self.main_win = main
        self.setObjectName("GameCreateWidget")

        h_layout = QHBoxLayout()

        form_layout = QFormLayout()
        form_layout.setContentsMargins(20, 50, 20, 50)

        self.game_name_value = QLineEdit()
        form_layout.addRow("游戏名称：", self.game_name_value)

        self.game_desc_value = QTextEdit()
        form_layout.addRow("游戏简介：", self.game_desc_value)

        self.game_appid_value = QLineEdit()
        form_layout.addRow("游戏ID：", self.game_appid_value)

        self.game_appkey_value = QLineEdit()
        form_layout.addRow("客户端Key：", self.game_appkey_value)

        h_layout2 = QHBoxLayout()
        self.keystore_path = QLineEdit()
        select_key_btn = QPushButton("浏览")
        select_key_btn.setStyleSheet('QPushButton{border-radius: 0px;}')
        select_key_btn.clicked.connect(self.select_keystore)
        h_layout2.addWidget(self.keystore_path)
        h_layout2.addWidget(select_key_btn)
        form_layout.addRow("KeyStore:", h_layout2)

        self.keystore_pwd_value = QLineEdit()
        form_layout.addRow("KeyPass:", self.keystore_pwd_value)

        self.keystore_alias_value = QLineEdit()
        form_layout.addRow("Alias:", self.keystore_alias_value)

        self.keystore_aliaspwd_value = QLineEdit()
        form_layout.addRow("AliasPass:", self.keystore_aliaspwd_value)

        h_layout.addLayout(form_layout, 3)

        v_layout2 = QVBoxLayout()
        v_layout2.addStretch(2)
        self.icon_img = QLabel()
        self.icon_img.setMaximumSize(QtCore.QSize(200, 200))
        self.icon_img.setMinimumSize(QtCore.QSize(200, 200))
        self.icon_img.setPixmap(QPixmap('icon.png'))
        self.icon_img.setScaledContents(True)
        v_layout2.addWidget(self.icon_img)
        icon_add_btn = QPushButton("添加Icon")
        icon_add_btn.setFixedWidth(100)
        icon_add_btn.clicked.connect(self.add_icon)
        v_layout2.addWidget(icon_add_btn, alignment=Qt.AlignHCenter)
        v_layout2.addStretch(6)
        create_btn = QPushButton("创 建")
        create_btn.setFixedWidth(100)
        create_btn.clicked.connect(self.create)
        v_layout2.addWidget(create_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        v_layout2.addStretch(1)
        if len(self.main_win.games) > 0:
            back_btn = QPushButton("返 回")
            back_btn.setFixedWidth(100)
            back_btn.clicked.connect(self.back)
            v_layout2.addWidget(back_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        else:
            back_btn = QPushButton("退 出")
            back_btn.setFixedWidth(100)
            back_btn.clicked.connect(self.main_win.close)
            v_layout2.addWidget(back_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        h_layout.addLayout(v_layout2, 1)

        self.setLayout(h_layout)
        self.game = {}
        self.icon_path = None

    def select_keystore(self):
        fname = QFileDialog.getOpenFileName(self, '选择签名文件', os.path.join(os.path.expanduser('~'), "Desktop"))
        if fname[0]:
            self.keystore_path.setText(fname[0])
            self.keystore_pwd_value.clear()
            self.keystore_alias_value.clear()
            self.keystore_aliaspwd_value.clear()

    def add_icon(self):
        fname = QFileDialog.getOpenFileName(self, '选择icon', os.path.join(os.path.expanduser('~'), "Desktop"), ("Images (*.png)"))
        if fname[0]:
            pix = QPixmap(fname[0])
            if pix.width() != 512 or pix.height() != 512:
                QMessageBox.warning(self, "警告", "必须上传512*512.png图片")
                return
            self.icon_img.setPixmap(pix)
            self.icon_path = fname[0]

    def back(self):
        self.main_win.set_game_list_widget(self.main_win.games)

    def create(self):
        if self.game_name_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "游戏名称不能为空！")
            return
        if self.game_appid_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "游戏Id不能为空！")
            return
        if self.game_appkey_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "客户端Key不能为空！")
            return
        if self.keystore_path.text().strip() == "":
            QMessageBox.warning(self, "警告", "必须上传keystore签名文件！")
            return
        if self.keystore_pwd_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "keystore密码不能为空！")
            return
        if self.keystore_alias_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "alias不能为空！")
            return
        if self.keystore_aliaspwd_value.text().strip() == "":
            QMessageBox.warning(self, "警告", "alias密码不能为空！")
            return
        self.game['name'] = self.game_name_value.text().strip()
        self.game['desc'] = self.game_desc_value.toPlainText().strip()
        self.game['id'] = self.game_appid_value.text().strip()
        self.game['key'] = self.game_appkey_value.text().strip()
        if os.path.exists(Utils.get_full_path('games/' + self.game['id'])):
            QMessageBox.warning(self, "警告", "游戏已存在！")
            return
        if not os.path.exists(Utils.get_full_path('games')):
            os.makedirs(Utils.get_full_path('games'))
        os.mkdir(Utils.get_full_path('games/' + self.game['id']))

        keystore = os.path.basename(self.keystore_path.text().strip())
        self.game['keystore'] = keystore
        self.game['keypwd'] = self.keystore_pwd_value.text().strip()
        self.game['alias'] = self.keystore_alias_value.text().strip()
        self.game['aliaspwd'] = self.keystore_aliaspwd_value.text().strip()
        os.mkdir(Utils.get_full_path('games/' + self.game['id'] + '/keystore'))
        keystore_path = Utils.get_full_path('games/' + self.game['id'] + '/keystore/' + keystore)
        Utils.copy_file(self.keystore_path.text().strip(), keystore_path)

        os.mkdir(Utils.get_full_path('games/' + self.game['id'] + '/icon'))
        if self.icon_path is not None:
            icon_file = Utils.get_full_path('games/' + self.game['id'] + '/icon/icon.png')
            Utils.copy_file(self.icon_path, icon_file)

        self.main_win.games.append(self.game)
        Utils.add_game(Utils.get_full_path('games/games.xml'), self.game)
        self.main_win.game_index = len(self.main_win.games)-1
        self.main_win.set_game_list_widget(self.main_win.games)
