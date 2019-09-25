# -*- coding: utf-8 -*-

import os
import os.path
import re
import subprocess
import sys
from xml.etree import ElementTree as ET

from scripts import LogUtils


def get_py_version():
    version = sys.version_info
    major = version.major
    minor = version.minor
    micro = version.micro
    curr_version = str(major) + '.' + str(minor) + '.' + str(micro)
    return curr_version


def get_full_path(filename):
    if os.path.isabs(filename):
        return filename
    cur_dir = os.path.dirname(os.getcwd())
    filename = os.path.join(cur_dir, filename)
    filename = filename.replace('\\', '/')
    filename = re.sub('/+', '/', filename)
    return filename


def del_file(src):
    if os.path.exists(src):
        if os.path.isfile(src):
            try:
                src = src.replace('\\', '/')
                os.remove(src)
            except Exception as e:
                LogUtils.error('delete file exception!\n%s', e.__str__())
                return 1
        elif os.path.isdir(src):
            for f in os.listdir(src):
                item_src = os.path.join(src, f)
                del_file(item_src)
            os.rmdir(src)
    return 0


def copy_file(src, dest):
    if not os.path.exists(src):
        LogUtils.error('the src is not exists.path:' + src)
        return 1
    if os.path.isfile(src):
        try:
            dest_file_stream = open(dest, 'wb')
            source_file_stream = open(src, 'rb')
            dest_file_stream.write(source_file_stream.read())
            dest_file_stream.close()
            source_file_stream.close()
        except Exception as e:
            LogUtils.error('copy file exception!\n%s', e.__str__())
            return 1
    else:
        if not os.path.exists(dest):
            os.mkdir(dest)
        for f in os.listdir(src):
            source_file = src + "/" + f
            target_file = dest + "/" + f
            copy_file(source_file, target_file)
    return 0


def list_files(src, res_files, ignore_files):
    if os.path.exists(src):
        if os.path.isfile(src) and src not in ignore_files:
            res_files.append(src)
        elif os.path.isdir(src):
            for f in os.listdir(src):
                if src not in ignore_files:
                    list_files(os.path.join(src, f), res_files, ignore_files)
    return res_files


def get_games(config_path):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        games = root.findall('game')
        if games is None or len(games) <= 0:
            return None
        game_list = []
        for cNode in games:
            game = {}
            params = cNode.findall('param')
            for cParam in params:
                key = cParam.get('name')
                val = cParam.get('value')
                game[key] = val

            game_list.append(game)
        return game_list
    except Exception as e:
        LogUtils.error('==> can not parse games.xml: %s', config_path)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return None


def update_games(config_path, game, index):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        games = root.findall('game')
        game_node = games[index]
        params = game_node.findall('param')
        for param_node in params:
            key = param_node.get('name')
            param_node.set('value', game[key])
        indent(root)
        tree = ET.ElementTree(root)
        tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')
        return True
    except Exception as e:
        LogUtils.error('==> can not parse games.xml: %s', config_path)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return False


def add_game(config_path, game):
    if not os.path.exists(config_path):
        root = ET.Element('games')
    else:
        tree = ET.parse(config_path)
        root = tree.getroot()
    game_node = ET.SubElement(root, 'game')
    for param in game:
        param_node = ET.SubElement(game_node, 'param')
        param_node.set('name', param)
        param_node.set('value', game[param])
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')


def indent(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def get_channels(config_path):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        channels = root.findall('channel')
        if channels is None or len(channels) <= 0:
            return None
        channel_list = []
        for cNode in channels:
            channel = {}
            params = cNode.findall('param')
            for cParam in params:
                key = cParam.get('name')
                val = cParam.get('value')
                channel[key] = val

            sdk_params = {}
            sdk_params_node = cNode.find('sdk-params')
            if sdk_params_node is not None:
                sdk_param_nodes = sdk_params_node.findall('param')
                if sdk_param_nodes is not None and len(sdk_param_nodes) > 0:
                    for cParam in sdk_param_nodes:
                        key = cParam.get('name')
                        val = cParam.get('value')
                        sdk_params[key] = val
            ret = set_channel_params(channel, sdk_params)
            if ret:
                channel_list.append(channel)
        return channel_list
    except Exception as e:
        LogUtils.error('=> can not parse config.xml: %s', config_path)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return None


def set_channel_params(channel, sdk_params):
    config_file = get_full_path('channelsdk/' + channel['sdk'] + '/config.xml')
    if not os.path.exists(config_file):
        LogUtils.error(' => the %s config.xml is not exists path: %s', channel['name'], config_file)
        return False
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
        channel['sdkParams'] = []
        param_nodes = root.find('params')
        for param_node in param_nodes:
            param = {}
            param['name'] = param_node.get('name')
            key = param_node.get('name')
            if key in sdk_params and sdk_params[key] is not None:
                param['value'] = sdk_params[key]
            else:
                LogUtils.info(' => the sdk %s have a new parameter: %s', channel['name'], key)
                param['value'] = ""
            param['showName'] = param_node.get('showName')
            param['writeIn'] = param_node.get('writeIn')
            channel['sdkParams'].append(param)

        channel['plugins'] = []
        plugin_nodes = root.find('plugins')
        for p_node in plugin_nodes:
            p = {}
            p['name'] = p_node.get('name')
            p['type'] = p_node.get('type')
            channel['plugins'].append(p)

        version_node = root.find('version')
        version_update_time = version_node.find('updateTime')
        channel['sdkUpdateTime'] = version_update_time.text
        version_name_node = version_node.find('versionName')
        channel['sdkVersionName'] = version_name_node.text
        return True
    except Exception as e:
        LogUtils.error(' => can not parse config.xml: %s', config_file)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return False


def add_channel(config_path, channel):
    if not os.path.exists(config_path):
        root = ET.Element('channels')
    else:
        tree = ET.parse(config_path)
        root = tree.getroot()
    channel_node = ET.SubElement(root, 'channel')
    for param in channel:
        if param == 'sdkParams':
            sdk_params_node = ET.SubElement(channel_node, 'sdk-params')
            for p in channel[param]:
                p_node = ET.SubElement(sdk_params_node, 'param')
                p_node.set('name', p['name'])
                p_node.set('value', p['value'])
            continue
        if param == 'plugins' or param == 'sdkUpdateTime' or param == 'sdkVersionName':
            continue
        param_node = ET.SubElement(channel_node, 'param')
        param_node.set('name', param)
        param_node.set('value', channel[param])
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')


def update_channels(config_path, channel, index):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        channels = root.findall('channel')
        channel_node = channels[index]
        params = channel_node.findall('param')
        for param_node in params:
            key = param_node.get('name')
            param_node.set('value', channel[key])

        channel_node.remove(channel_node.find('sdk-params'))
        sdk_params_node = ET.SubElement(channel_node, 'sdk-params')
        for p in channel['sdkParams']:
            p_node = ET.SubElement(sdk_params_node, 'param')
            p_node.set('name', p['name'])
            p_node.set('value', p['value'])

        indent(root)
        tree = ET.ElementTree(root)
        tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')
        return True
    except Exception as e:
        LogUtils.error('=> can not parse config.xml path: %s', config_path)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return False


def del_channel(config_path, index):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        channels = root.findall('channel')
        root.remove(channels[index])
        indent(root)
        tree = ET.ElementTree(root)
        tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')
    except Exception as e:
        LogUtils.error('=> can not parse config.xml path: %s', config_path)
        LogUtils.error('parse xml exception!\n%s', e.__str__())


def get_channel_config(channel):
    config_file = get_full_path('channelsdk/' + channel['sdk'] + '/config.xml')
    if not os.path.exists(config_file):
        LogUtils.error(' => the %s config.xml is not exists path: %s', channel['name'], config_file)
        return False
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
        channel['name'] = root.get('name')
        channel['sdkParams'] = []
        param_nodes = root.find('params')
        for param_node in param_nodes:
            param = {}
            param['name'] = param_node.get('name')
            param['showName'] = param_node.get('showName')
            param['writeIn'] = param_node.get('writeIn')
            channel['sdkParams'].append(param)

        channel['plugins'] = []
        plugin_nodes = root.find('plugins')
        for p_node in plugin_nodes:
            p = {}
            p['name'] = p_node.get('name')
            p['type'] = p_node.get('type')
            channel['plugins'].append(p)

        version_node = root.find('version')
        version_update_time = version_node.find('updateTime')
        channel['sdkUpdateTime'] = version_update_time.text
        version_name_node = version_node.find('versionName')
        channel['sdkVersionName'] = version_name_node.text
        return True
    except Exception as e:
        LogUtils.error(' => can not parse config.xml path: %s', config_file)
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return False


def get_local_config():
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        LogUtils.error('config.ini is not exists. ==> ' + config_file)
        return None
    cf = open(config_file, 'r', encoding='utf-8-sig')
    lines = cf.readlines()
    cf.close()
    config = {}
    for line in lines:
        if line.startswith('#') or len(line.strip()) <= 0:
            continue
        line = line.strip()
        dup = line.split('=')
        config[dup[0]] = dup[1]
    return config


def write_developer_properties(game, channel, target_file_path):
    config = get_local_config()
    if config is None:
        return 1
    pro_str = 'YINHU_SDK_VERSION_CODE=' + config['YINHU_SDK_VERSION_CODE'] + '\n'
    pro_str = pro_str + 'YINHU_APPID=' + game['id'] + '\n'
    pro_str = pro_str + 'YINHU_APPKEY=' + game['key'] + '\n'
    pro_str = pro_str + 'YINHU_Channel=' + channel['channelId'] + '\n'
    pro_str = pro_str + 'YINHU_AUTH_URL=' + config['YINHU_AUTH_URL'] + '\n'
    pro_str = pro_str + 'DEBUG_MODES=' + channel['debug'] + '\n'
    if channel['sdkParams'] is not None and len(channel['sdkParams']) > 0:
        for param in channel['sdkParams']:
            if param['writeIn'] == '2':
                pro_str = pro_str + param['name'] + '=' + param['value'] + '\n'

    LogUtils.info('the develop info is:\n%s', pro_str)
    target_file = open(target_file_path, 'w', encoding='utf-8')
    target_file.write(pro_str)
    target_file.close()
    return 0


def write_plugin_config(channel, plugin_path):
    if 'plugins' not in channel:
        LogUtils.error("%s SDK no plugins", channel['sdk'])
        return 1
    try:
        root = ET.Element('plugins')
        for plugin in channel['plugins']:
            param_node = ET.SubElement(root, 'plugin')
            param_node.set('name', plugin['name'])
            param_node.set('type', plugin['type'])
        indent(root)
        tree = ET.ElementTree(root)
        tree.write(plugin_path, xml_declaration=True, encoding='utf-8', method='xml')
        return 0
    except Exception as e:
        LogUtils.error("write plugins.xml exception")
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return 1


def exec_cmd(cmd):
    try:
        LogUtils.info('*********************cmd start***********************')
        cmd = cmd.replace('\\', '/')
        cmd = re.sub('/+', '/', cmd)
        st = subprocess.STARTUPINFO
        st.dwFlags = subprocess.STARTF_USESHOWWINDOW
        st.wShowWindow = subprocess.SW_HIDE
        LogUtils.info('cmd: %s', cmd)
        sub = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code, std, err = sub.returncode, sub.stdout, sub.stderr
        if code:
            LogUtils.error('===>exec Fail<===')
            LogUtils.error("\n" + err.decode('gbk'))
        else:
            # LogUtils.info(std.decode('gbk'))
            LogUtils.info('===>exec success<===')
        return code
    except Exception as e:
        LogUtils.error('===>exec Fail<===')
        LogUtils.error('Exception:' + e.__str__())
        return 1
    finally:
        LogUtils.info('*********************cmd end***********************')


def exec_cmd2(cmd):
    try:
        LogUtils.info('*********************cmd start***********************')
        cmd = cmd.replace('\\', '/')
        cmd = re.sub('/+', '/', cmd)
        st = subprocess.STARTUPINFO
        st.dwFlags = subprocess.STARTF_USESHOWWINDOW
        st.wShowWindow = subprocess.SW_HIDE
        LogUtils.info('cmd: %s', cmd)
        sub = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code, std, err = sub.returncode, sub.stdout, sub.stderr
        if code:
            LogUtils.error('===>exec Fail<===')
            LogUtils.error("\n" + err.decode('gbk'))
            return None
        else:
            return std.decode('utf-8')
    except Exception as e:
        LogUtils.error('===>exec Fail<===')
        LogUtils.error('Exception:' + e.__str__())
        return None
    finally:
        LogUtils.info('*********************cmd end***********************')
