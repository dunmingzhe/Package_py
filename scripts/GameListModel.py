# -*- coding: utf-8 -*-

import os.path
from PyQt5.QtCore import QAbstractListModel, Qt, QVariant, QSize, QModelIndex
from PyQt5.QtGui import QFont, QIcon
from scripts import Utils


class GameListModel(QAbstractListModel):
    def __init__(self, games):
        super().__init__()
        self.games = games

    def data(self, index, role):
        if index.isValid() or (0 <= index.row() < len(self.ListItemData)):
            if role == Qt.DisplayRole:
                return QVariant(self.games[index.row()]['id'])
            elif role == Qt.DecorationRole:
                icon = self.games[index.row()]['id']
                icon = Utils.get_full_path('games/' + icon + '/icon/icon.png')
                if not os.path.exists(icon):
                    icon = 'icon.png'
                return QVariant(QIcon(icon))
            elif role == Qt.SizeHintRole:
                return QVariant(QSize(80, 80))
            elif role == Qt.TextAlignmentRole:
                return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
            elif role == Qt.FontRole:
                font = QFont()
                font.setPixelSize(16)
                font.setFamily("Microsoft YaHei")
                return QVariant(font)
            else:
                return QVariant()

    def rowCount(self, parent=QModelIndex()):
        return len(self.games)

    def add_item(self, item_data):
        if item_data:
            self.beginInsertRows(QModelIndex(), len(self.games), len(self.games) + 1)
            self.games.append(item_data)
            self.endInsertRows()

    def delete_item(self, index):
        if -1 < index < len(self.games):
            del self.games[index]

    def update_item(self, index, game):
        if -1 < index < len(self.games):
            self.games[index] = game

    def get_item(self, index):
        if -1 < index < len(self.games):
            return self.games[index]
