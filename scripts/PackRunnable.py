# -*- coding: utf-8 -*-
import os
import threading
import time
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject

from scripts import LogUtils, Utils, ApkUtils


class Signal(QObject):
    signal = pyqtSignal(str, int, str, int)


class PackRunnable(QRunnable):

    is_close = False

    def __init__(self, game, channel, apk):
        super().__init__()
        self.game = game
        self.channel = channel
        self.apk = apk
        self.signal = Signal()

    def run(self):
        # 清空已有的workspace
        work_dir = Utils.get_full_path('workspace/' + self.game['id'] + '/' + self.channel['channelId'])
        Utils.del_file(work_dir)
        os.makedirs(work_dir)
        # 用线程id，一一对应，标识logger日志输出路径
        thread_id = threading.get_ident()
        logger = LogUtils.Logger(str(thread_id), work_dir).get_logger()
        LogUtils.add_logger(thread_id, logger)

        LogUtils.info('Current Selected Game ID is : %s, with SDK is : %s', self.game['id'], self.channel['sdk'])
        LogUtils.info('game:\n%s', self.game)
        LogUtils.info('channel:\n%s', self.channel)

        src_apk_path = work_dir + '/songshu.apk'
        # 复制上传母包到workspace
        result = Utils.copy_file(self.apk, src_apk_path)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制母包文件失败，详情查看log.log", 5)
            if result:
                return
        # 反编译母包
        decompile_dir = work_dir + '/decompile'
        frame_work_dir = work_dir + '/framework'
        result = ApkUtils.decompile_apk(src_apk_path, decompile_dir, frame_work_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "反编译母包异常，详情查看log.log", 15)
            if result:
                return

        # 复制sdk资源到工作目录
        sdk_source_dir = Utils.get_full_path('channelsdk/' + self.channel['sdk'])
        sdk_dest_dir = work_dir + '/sdk'
        result = Utils.copy_file(sdk_source_dir, sdk_dest_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制SDK文件夹失败，详情查看log.log", 18)
            if result:
                return
        # 将插件里的jar资源转dex
        result = ApkUtils.jar2dex(sdk_source_dir, sdk_dest_dir + '/classes.dex')
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "渠道jar转dex异常，详情查看log.log", 25)
            if result:
                return
        # 将插件里的dex资源转smali，合并到母包反编译目录中
        result = ApkUtils.dex2smali(sdk_dest_dir + '/classes.dex', decompile_dir + '/smali', '')
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "渠道dex转smali异常，详情查看log.log", 28)
            if result:
                return

        # 合并manifest文件
        result = ApkUtils.merge_manifest(decompile_dir, sdk_dest_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "合并manifest文件失败，详情查看log.log", 30)
            if result:
                return
        # 复制插件libs里的so库
        ApkUtils.copy_libs(decompile_dir, sdk_dest_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制libs文件夹失败，详情查看log.log", 33)
        # 复制插件assets文件夹
        result = Utils.copy_file(sdk_dest_dir + '/assets', decompile_dir + '/assets')
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制assets文件夹失败，详情查看log.log", 35)
            if result:
                return
        # 复制插件res文件夹
        result = Utils.copy_file(sdk_dest_dir + '/res', decompile_dir + '/res')
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制res文件夹失败，详情查看log.log", 38)
            if result:
                return

        # 复制渠道特殊配置资源，比如，针对个别渠道设置的loading页或logo
        ApkUtils.copy_ext_res(self.game, self.channel, decompile_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "复制渠道特殊文件夹失败，详情查看log.log", 40)

        # 将游戏原来的包名替换成渠道里面的包名，四大组件也会按照相关规则替换包名
        package_name = ApkUtils.rename_package_name(decompile_dir, self.channel['package'])
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], 0, "", 45)

        # 给对应的icon添加角标
        ApkUtils.append_channel_mark(self.game, sdk_dest_dir, decompile_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], 0, "", 50)
        # 配置参数写入
        result = ApkUtils.write_develop_info(self.game, self.channel, decompile_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "写入配置参数失败，详情查看log.log", 52)
            if result:
                return
        # 如果主sdk有特殊的逻辑。执行特殊的逻辑脚本。
        result = ApkUtils.do_sdk_script(self.channel, decompile_dir, package_name, sdk_dest_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "执行渠道脚本异常，详情查看log.log", 55)
            if result:
                return
        # 修改游戏名称，并将meta-data写入manifest文件
        ApkUtils.modify_manifest(self.channel, decompile_dir, package_name)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "", 60)
        # 重新生成R文件，并导入到包名下
        result = ApkUtils.generate_r_file(package_name, decompile_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "重新生成R文件异常，详情查看log.log", 75)
            if result:
                return

        # 修改apktool.yml里的压缩配置，防止包体变大
        ApkUtils.edit_yml(self.channel, decompile_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "", 80)
        # 回编译生成apk
        target_apk = work_dir + '/output.apk'
        result = ApkUtils.recompile_apk(decompile_dir, target_apk, frame_work_dir)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "回编译APK异常，详情查看log.log", 90)
            if result:
                return
        # 复制添加资源到apk
        ApkUtils.copy_root_res_files(target_apk, decompile_dir)
        # apk签名（v1签名）
        result = ApkUtils.sign_apk(self.game, target_apk)
        if self.is_close:
            return
        else:
            self.signal.signal.emit(self.channel['channelId'], result, "渠道包签名异常，详情查看log.log", 98)
            if result:
                return
        # apk对齐
        dest_apk_name = self.game['name'] + '-' + self.channel['name'] + '-' + time.strftime('%Y%m%d%H') + '.apk'
        dest_apk_dir = Utils.get_full_path('output/' + self.game['id'] + '/' + self.channel['name'])
        if not os.path.exists(dest_apk_dir):
            os.makedirs(dest_apk_dir)
        dest_apk = dest_apk_dir + '/' + dest_apk_name
        result = ApkUtils.zipalign_apk(target_apk, dest_apk)
        if self.is_close:
            pass
        else:
            if result == 0:
                self.signal.signal.emit(self.channel['channelId'], result, dest_apk_dir, 100)
            else:
                self.signal.signal.emit(self.channel['channelId'], result, "apk包体4k对齐异常，详情查看log.log", 100)

        # Utils.exec_cmd('start ' + dest_apk_dir)
        # LogUtils.info('package success. ==>>>> APK Path:' + dest_apk)
