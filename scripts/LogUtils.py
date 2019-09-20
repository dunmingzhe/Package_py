# -*- coding: utf-8 -*-
import logging
import os
import threading
'''
日志分流：
用线程id（可以理解为当前打包任务id）标识logger对象，并与日志输出路径一一对应，
只输出当前单个任务的日志
'''
loggers = {}


def add_logger(dir=os.getcwd()):
    logger = logging.getLogger(str(threading.get_ident()))
    logger.setLevel(logging.DEBUG)
    log_path = dir + "/log.log"
    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(log_path, 'w', encoding='utf-8')
    fh.setLevel(logging.INFO)

    # 再创建一个handler，用于输出到控制台
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)

    # 定义handler的输出格式
    formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s]%(message)s')
    fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    # 给logger添加handler
    logger.addHandler(fh)
    # self.logger.addHandler(ch)
    fh.close()
    # ch.close()
    loggers[threading.get_ident()] = logger


def info(msg, *args):
    logger = loggers[threading.get_ident()]
    logger.info(msg, *args)


def debug(msg, *args):
    logger = loggers[threading.get_ident()]
    logger.debug(msg, *args)


def warning(msg, *args):
    logger = loggers[threading.get_ident()]
    logger.warning(msg, *args)


def error(msg, *args):
    logger = loggers[threading.get_ident()]
    logger.error(msg, *args)


# 打包任务完成，关闭filehandler的流，移除filehandler
def close():
    logger = loggers[threading.get_ident()]
    logger.handlers[0].stream.close()
    logger.removeHandler(logger.handlers[0])
