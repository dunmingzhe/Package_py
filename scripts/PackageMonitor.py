# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal
'''
打包任务监听线程
通过轮询判断任务线程池活跃线程数，来判断打包是否完成（或被取消）
'''


class PackageMonitor(QThread):
    signal = pyqtSignal()

    def __init__(self, pool):
        super().__init__()
        self.pool = pool

    def run(self):
        flag = True
        while flag:
            count = self.pool.activeThreadCount()
            # 打包完成，发完成信号，重置flag，终止线程
            if count <= 0:
                self.signal.emit()
                flag = False
            # 打包进行中，线程休眠
            else:
                print(count)
                QThread.sleep(3)
