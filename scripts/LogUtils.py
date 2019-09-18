# -*- coding: utf-8 -*-
import logging
import os
import threading


class Logger(object):

    def __init__(self, name=None, dir=os.getcwd()):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_path = dir + "/log.log"
        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(self.log_path, 'w', encoding='utf-8')
        fh.setLevel(logging.INFO)

        # 再创建一个handler，用于输出到控制台
        # ch = logging.StreamHandler()
        # ch.setLevel(logging.INFO)

        # 定义handler的输出格式
        formatter = logging.Formatter(
            '[%(asctime)s]:[%(levelname)s]%(message)s')
        fh.setFormatter(formatter)
        # ch.setFormatter(formatter)
        # 给logger添加handler
        self.logger.addHandler(fh)
        # self.logger.addHandler(ch)
        fh.close()
        # ch.close()

    def get_logger(self):
        return self.logger


dic = {}


def add_logger(thread_id, logger):
    dic[thread_id] = logger


def info(msg, *args):
    logger = dic[threading.get_ident()]
    logger.info(msg, *args)


def debug(msg, *args):
    logger = dic[threading.get_ident()]
    logger.debug(msg, *args)


def warning(msg, *args):
    logger = dic[threading.get_ident()]
    logger.warning(msg, *args)


def error(msg, *args):
    logger = dic[threading.get_ident()]
    logger.error(msg, *args)

# TODO 当前打包任务完成，关闭filehandler的流
