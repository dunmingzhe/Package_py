# -*- coding: utf-8 -*-
import sys, os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.Qt import QApplication, QFile, QTextStream
from scripts.MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    file = QFile("dark.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    mainWin.setStyleSheet(stream.readAll())
    mainWin.show()
    sys.exit(app.exec_())


