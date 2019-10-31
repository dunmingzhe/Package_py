# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import QThreadPool, QThread, QRunnable, pyqtSignal, QObject, QDateTime
from scripts import LogUtils, Utils, ApkUtils


# 打包任务监听线程
# 通过轮询判断任务线程池活跃线程数，来判断打包是否完成（或被取消）
class PackageMonitor(QThread):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.globalInstance()
        self.pool.setMaxThreadCount(3)

    def run(self):
        flag = True
        while flag:
            count = self.pool.activeThreadCount()
            if count <= 0:  # 打包完成，发完成信号，重置flag，终止线程
                self.signal.emit()
                flag = False
            else:   # 打包进行中，线程休眠
                QThread.sleep(3)

    def add_runnable(self, runnable):
        self.pool.start(runnable)

    def clear(self):
        self.pool.clear()


# 打包任务线程发出信号，因为QRunnable不是继承QObject，没有信号机制，所以需借助此类
class Signal(QObject):
    signal = pyqtSignal(str, int, str, int)


# 打包任务线程，执行单一打包任务
class PackRunnable(QRunnable):

    is_close = False

    def __init__(self, game, channel, apk):
        super().__init__()
        self.game = game
        self.channel = channel
        self.apk = apk
        self.signal = Signal()

    def run(self):
        # 开启任务，发送打包信号
        self.signal.signal.emit(self.channel['channelId'], 0, "正在打包......", 0)
        # 清空已有的workspace
        work_dir = Utils.get_full_path('workspace/' + self.game['id'] + '/' + self.channel['channelId'])
        Utils.del_file(work_dir)
        os.makedirs(work_dir)
        # 生成当前打包任务的logger，添加到字典
        LogUtils.add_logger(work_dir)

        LogUtils.info('Current Selected Game ID is : %s, with SDK is : %s', self.game['id'], self.channel['sdk'])
        LogUtils.info('game:\n%s', self.game)
        LogUtils.info('channel:\n%s', self.channel)

        src_apk_path = work_dir + '/songshu.apk'
        # 复制上传母包到workspace
        result = Utils.copy_file(self.apk, src_apk_path)
        if self.flag(result, "打包失败：复制母包文件失败，详情查看log.log", 5):
            return

        # 反编译母包
        decompile_dir = work_dir + '/decompile'
        frame_work_dir = work_dir + '/framework'
        result = ApkUtils.decompile_apk(src_apk_path, decompile_dir, frame_work_dir)
        if self.flag(result, "打包失败：反编译母包异常，详情查看log.log", 15):
            return

        # 复制sdk资源到工作目录
        sdk_source_dir = Utils.get_full_path('channelsdk/' + self.channel['sdk'])
        sdk_dest_dir = work_dir + '/sdk'
        result = Utils.copy_file(sdk_source_dir, sdk_dest_dir)
        if self.flag(result, "打包失败：复制SDK文件夹失败，详情查看log.log", 18):
            return

        # 将插件里的jar资源转dex
        result = ApkUtils.jar2dex(sdk_source_dir, sdk_dest_dir + '/classes.dex')
        if self.flag(result, "打包失败：渠道jar转dex异常，详情查看log.log", 25):
            return

        # 将插件里的dex资源转smali，合并到母包反编译目录中
        result = ApkUtils.dex2smali(sdk_dest_dir + '/classes.dex', decompile_dir + '/smali', '')
        if self.flag(result, "打包失败：渠道dex转smali异常，详情查看log.log", 28):
            return

        # 合并manifest文件
        result = ApkUtils.merge_manifest(decompile_dir, sdk_dest_dir)
        if self.flag(result, "打包失败：合并manifest文件失败，详情查看log.log", 30):
            return

        # 复制插件libs里的so库
        ApkUtils.copy_libs(decompile_dir, sdk_dest_dir)
        if self.flag(0, "", 33):
            return

        # 复制插件assets文件夹
        result = Utils.copy_file(sdk_dest_dir + '/assets', decompile_dir + '/assets')
        if self.flag(result, "打包失败：复制assets文件夹失败，详情查看log.log", 35):
            return

        # 复制插件res文件夹
        result = Utils.copy_file(sdk_dest_dir + '/res', decompile_dir + '/res')
        if self.flag(result, "打包失败：复制res文件夹失败，详情查看log.log", 38):
            return

        # 复制渠道特殊配置资源，比如，针对个别渠道设置的loading页或logo
        ApkUtils.copy_ext_res(self.game, decompile_dir)
        if self.flag(0, "", 40):
            return

        # 将游戏原来的包名替换成渠道里面的包名，四大组件也会按照相关规则替换包名
        package_name = ApkUtils.rename_package_name(decompile_dir, self.channel['package'])
        if self.flag(0, "", 45):
            return

        # 给对应的icon添加角标
        ApkUtils.append_channel_mark(self.game, sdk_dest_dir, decompile_dir)
        if self.flag(0, "", 50):
            return

        # 配置参数写入
        result = ApkUtils.write_develop_info(self.game, self.channel, decompile_dir)
        if self.flag(result, "打包失败：写入配置参数失败，详情查看log.log", 52):
            return

        # 如果主sdk有特殊的逻辑。执行特殊的逻辑脚本。
        result = ApkUtils.do_sdk_script(self.channel, decompile_dir, package_name, sdk_dest_dir)
        if self.flag(result, "打包失败：执行渠道脚本异常，详情查看log.log", 55):
            return

        # 修改游戏名称，并将meta-data写入manifest文件
        ApkUtils.modify_manifest(self.channel, decompile_dir, package_name)
        if self.flag(0, "", 60):
            return

        # 重新生成R文件，并导入到包名下
        result = ApkUtils.generate_r_file(package_name, decompile_dir)
        if self.flag(result, "打包失败：重新生成R文件异常，详情查看log.log", 75):
            return

        # 防止方法数超65535，判断是否分dex
        result = ApkUtils.classes_split(decompile_dir, sdk_dest_dir)
        if self.flag(result, "打包失败：分dex出现异常，详情查看log.log", 78):
            return

        # 修改apktool.yml里的压缩配置，防止包体变大
        ApkUtils.edit_yml(self.channel, decompile_dir)
        if self.flag(0, "", 80):
            return

        # 回编译生成apk
        target_apk = work_dir + '/output.apk'
        result = ApkUtils.recompile_apk(decompile_dir, target_apk, frame_work_dir)
        if self.flag(result, "打包失败：回编译APK异常，详情查看log.log", 90):
            return

        # 复制添加资源到apk
        result = ApkUtils.copy_root_ext_files(target_apk, decompile_dir)
        if self.flag(result, "打包失败：母包其余资源导入异常，详情查看log.log", 92):
            return

        # apk签名（v1签名）
        result = ApkUtils.sign_apk(self.game, target_apk)
        if self.flag(result, "打包失败：渠道包签名异常，详情查看log.log", 98):
            return

        # apk对齐
        time_str = QDateTime.currentDateTime().toString("yyyyMMddhhmm")
        dest_apk_name = self.game['name'] + '-' + self.channel['name'] + '-' + time_str + '.apk'
        dest_apk_dir = Utils.get_full_path('output/' + self.game['id'] + '/' + self.channel['channelId'])
        if not os.path.exists(dest_apk_dir):
            os.makedirs(dest_apk_dir)
        dest_apk = dest_apk_dir + '/' + dest_apk_name
        result = ApkUtils.align_apk(target_apk, dest_apk)
        if self.is_close:
            pass
        else:
            if result == 0:
                self.signal.signal.emit(self.channel['channelId'], 1, "打包成功：双击打开出包目录", 100)
            else:
                self.signal.signal.emit(self.channel['channelId'], result, "打包失败：apk包体4k对齐异常，详情查看log.log", 100)
        LogUtils.close()

    # 判断是否取消或打包异常的flag
    def flag(self, result, msg, step):
        if self.is_close:   # 取消打包，结束任务前，关闭logger文件流
            LogUtils.close()
            return True
        else:
            self.signal.signal.emit(self.channel['channelId'], result, msg, step)
            if result:  # 打包失败，结束任务前，关闭logger文件流
                LogUtils.close()
                return True
