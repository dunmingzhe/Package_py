# -*- coding: utf-8 -*-
import threading

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QMainWindow

from scripts import Utils, LogUtils
from scripts.ChannelAddWidget import ChannelAddWidget
from scripts.ChannelListWidget import ChannelListWidget
from scripts.GameCreateWidget import GameCreateWidget
from scripts.GameListWidget import GameListWidget
from scripts.PackageWidget import PackageWidget


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
