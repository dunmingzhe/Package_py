# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.Qt import QLabel, QMovie, QHBoxLayout, QVBoxLayout, QPushButton, QWidget


class MainWidget(QWidget):

    def __init__(self, main):
        super(MainWidget, self).__init__()
        self.main_win = main
        self.setObjectName("MainWidget")

        v_layout = QVBoxLayout()
        label = QLabel(self)
        label.setAlignment(Qt.AlignCenter)
        movie = QMovie("main_bg.gif")
        label.setMovie(movie)
        movie.start()
        v_layout.addWidget(label)
        h_layout = QHBoxLayout()
        btn1 = QPushButton("愛")
        btn1.setFixedWidth(30)
        btn1.clicked.connect(self.sub_pack)
        h_layout.addWidget(btn1, alignment=Qt.AlignLeft | Qt.AlignBottom)

        btn2 = QPushButton("嫌")
        btn2.setFixedWidth(30)
        btn2.clicked.connect(self.to_pack)
        h_layout.addWidget(btn2, alignment=Qt.AlignRight | Qt.AlignBottom)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)

    def sub_pack(self):
        print("ssssssss")

    def to_pack(self):
        if self.main_win.games is None or len(self.main_win.games) <= 0:
            self.main_win.set_create_game_widget([])
        else:
            self.main_win.set_game_list_widget(self.main_win.games)
