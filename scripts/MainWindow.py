# -*- coding: utf-8 -*-
import threading

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QMainWindow, QProgressDialog, QMessageBox, pyqtSignal

from scripts import Utils, LogUtils
from scripts.ChannelAddWidget import ChannelAddWidget
from scripts.ChannelListWidget import ChannelListWidget
from scripts.GameCreateWidget import GameCreateWidget
from scripts.GameListWidget import GameListWidget
from scripts.PackageWidget import PackageWidget
from scripts.PakcThread import PackThread


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        thread_id = threading.get_ident()
        logger = LogUtils.Logger("main").get_logger()
        LogUtils.add_logger(thread_id, logger)

        self.game_index = 0
        self.progress = None
        self.pack_thread = None

        self.setObjectName("MainWindow")
        self.resize(1000, 563)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setWindowIcon(QIcon('pack.ico'))
        self.games = Utils.get_games(Utils.get_full_path('games/games.xml'))
        if self.games is None:
            self.games = []
            self.set_create_game_widget(self.games)
        else:
            self.set_game_list_widget(self.games)

    def set_main_title(self, width, title):
        self.setMinimumSize(QtCore.QSize(width, 540))
        self.setMaximumSize(QtCore.QSize(width, 540))
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", title))

    def set_game_list_widget(self, games):
        self.games = games
        self.set_main_title(960, "游戏详情")
        self.setCentralWidget(GameListWidget(self))

    def set_create_game_widget(self, games):
        self.games = games
        self.set_main_title(800, "创建游戏")
        self.setCentralWidget(GameCreateWidget(self))

    def set_channel_list_widget(self, channels):
        self.set_main_title(960, "参数配置")
        self.setCentralWidget(ChannelListWidget(self, channels))

    def set_add_channel_widget(self, channels):
        self.set_main_title(800, "添加渠道")
        self.setCentralWidget(ChannelAddWidget(self, channels))

    def set_package_widget(self, channels):
        self.set_main_title(800, "渠道打包")
        self.setCentralWidget(PackageWidget(self, channels))

    def do_package(self, channel, apk):
        self.progress = QProgressDialog(self)
        self.progress.setFixedWidth(800)
        self.progress.setFixedHeight(100)
        self.progress.setWindowTitle("正在打包...")
        text = self.games[self.game_index]['name'] + " + " + channel['name'] + "渠道 出包中......"
        self.progress.setLabelText(text)
        self.progress.setCancelButtonText("取消")
        self.progress.canceled.connect(self.cancel)
        self.progress.setMinimumDuration(0)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setRange(0, 100)
        self.progress.setValue(1)
        self.pack_thread = PackThread(self.games[self.game_index], channel, apk)
        self.pack_thread.signal.connect(self.set_value)
        self.pack_thread.finished.connect(self.pack_thread.deleteLater)
        self.pack_thread.start()

    def set_value(self, result, msg, step):
        if result:
            # 出现异常，提示异常
            self.progress.cancel()
            QMessageBox.warning(self, "警告", msg)
        else:
            self.progress.setValue(step)

    def cancel(self):
        self.pack_thread.is_close = True
        QMessageBox.warning(self, "警告", "打包已取消")
