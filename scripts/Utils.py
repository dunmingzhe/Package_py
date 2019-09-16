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
            except:
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


def list_files(src, res_files, igore_files):
    if os.path.exists(src):
        if os.path.isfile(src) and src not in igore_files:
            res_files.append(src)
        elif os.path.isdir(src):
            for f in os.listdir(src):
                if src not in igore_files:
                    list_files(os.path.join(src, f), res_files, igore_files)

    return res_files


def get_games(config_path):
    """
        get all games
    """
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
    except:
        LogUtils.error('==> can not parse games.xml.path: %s', config_path)
        return None
    games = root.findall('game')
    if games is None or len(games) <= 0:
        return None
    game_list = []
    for cNode in games:
        game = {}
        params = cNode.findall('param')
        if params is not None and len(params) > 0:
            for cParam in params:
                key = cParam.get('name')
                val = cParam.get('value')
                game[key] = val

        game_list.append(game)

    return game_list


def update_games(config_path, games):
    root = ET.Element('games')
    for game in games:
        game_node = ET.SubElement(root, 'game')
        for param in game:
            param_node = ET.SubElement(game_node, 'param')
            param_node.set('name', param)
            param_node.set('value', game[param])
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')


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
    except:
        LogUtils.error('=> can not parse config.xml.path: %s', config_path)
        return None
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

        sdk_params = cNode.find('sdk-params')
        sdk_params2 = {}
        if sdk_params is not None:
            sdk_param_nodes = sdk_params.findall('param')
            if sdk_param_nodes is not None and len(sdk_param_nodes) > 0:
                for cParam in sdk_param_nodes:
                    key = cParam.get('name')
                    val = cParam.get('value')
                    sdk_params2[key] = val

        channel['params'] = sdk_params2
        ret = set_channel_params(channel)
        if ret:
            channel_list.append(channel)
    return channel_list


def set_channel_params(channel):
    config_file = get_full_path('channelsdk/' + channel['sdk'] + '/config.xml')
    if not os.path.exists(config_file):
        LogUtils.error('the config.xml is not exists of sdk %s.path:%s', channel['name'], config_file)
        return 0
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
    except:
        LogUtils.error('can not parse == config.xml.path:%s', config_file)
        return 0
    param_nodes = root.find('params')
    channel['sdkParams'] = []
    if param_nodes is not None and len(param_nodes) > 0:
        for param_node in param_nodes:
            param = {}
            param['name'] = param_node.get('name')
            key = param_node.get('name')
            if key in channel['params'] and channel['params'][key] is not None:
                param['value'] = channel['params'][key]
            else:
                LogUtils.debug("the sdk %s 'sdkParam's is not all configed in the config.xml.path:%s", channel['name'], config_file)
                return 0
            param['showName'] = param_node.get('showName')
            param['writeIn'] = param_node.get('writeIn')
            channel['sdkParams'].append(param)
    channel.pop('params')

    plugin_nodes = root.find('plugins')
    if plugin_nodes is not None and len(plugin_nodes) > 0:
        channel['plugins'] = []
        for p_node in plugin_nodes:
            p = {}
            p['name'] = p_node.get('name')
            p['type'] = p_node.get('type')
            channel['plugins'].append(p)

    version_node = root.find('version')
    if version_node is not None and len(version_node) > 0:
        version_update_time = version_node.find('updateTime')
        version_name_node = version_node.find('versionName')
        if version_update_time is not None and version_name_node is not None:
            channel['sdkUpdateTime'] = version_update_time.text
            channel['sdkVersionName'] = version_name_node.text
    return 1


def update_channels(config_path, channel, index):
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
    except:
        LogUtils.error('=> can not parse config.xml.path: %s', config_path)
        return None
    channels = root.findall('channel')

    params = channels[index].findall('param')
    for param_node in params:
        key = param_node.get('name')
        param_node.set('value', channel[key])

    sdk_param_nodes = channels[index].find('sdk-params').findall('param')
    for param_node in sdk_param_nodes:
        key = param_node.get('name')
        for param in channel['sdkParams']:
            if key == param['name']:
                param_node.set('value', param['value'])

    indent(root)
    tree = ET.ElementTree(root)
    tree.write(config_path, xml_declaration=True, encoding='utf-8', method='xml')


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


def get_channel_config(channel):
    config_file = get_full_path('channelsdk/' + channel['sdk'] + '/config.xml')
    if not os.path.exists(config_file):
        LogUtils.error('the config.xml is not exists of sdk %s.path:%s', channel['name'], config_file)
        return
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
    except:
        LogUtils.error('can not parse == config.xml.path:%s', config_file)
        return
    channel['name'] = root.get('name')
    channel['sdkParams'] = []
    param_nodes = root.find('params')
    if param_nodes is not None and len(param_nodes) > 0:
        for param_node in param_nodes:
            param = {}
            param['name'] = param_node.get('name')
            param['showName'] = param_node.get('showName')
            param['writeIn'] = param_node.get('writeIn')
            channel['sdkParams'].append(param)

    plugin_nodes = root.find('plugins')
    if plugin_nodes is not None and len(plugin_nodes) > 0:
        channel['plugins'] = []
        for p_node in plugin_nodes:
            p = {}
            p['name'] = p_node.get('name')
            p['type'] = p_node.get('type')
            channel['plugins'].append(p)

    version_node = root.find('version')
    if version_node is not None and len(version_node) > 0:
        version_update_time = version_node.find('updateTime')
        version_name_node = version_node.find('versionName')
        if version_update_time is not None and version_name_node is not None:
            channel['sdkUpdateTime'] = version_update_time.text
            channel['sdkVersionName'] = version_name_node.text


def get_local_config():
    config_file = get_full_path('config.ini')
    if not os.path.exists(config_file):
        LogUtils.error('local.properties is not exists. ==> ' + config_file)
        return None
    cf = open(config_file, 'r')
    lines = cf.readlines()
    cf.close()
    config = {}
    for line in lines:
        line = line.strip()
        dup = line.split('=')
        config[dup[0]] = dup[1]
    return config


def write_developer_properties(game, channel, target_file_path):
    config = get_local_config()
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

    LogUtils.debug('the develop info is:\n%s', pro_str)
    target_file = open(target_file_path, 'wb')
    pro_str = pro_str.encode('UTF-8')
    target_file.write(pro_str)
    target_file.close()


def write_plugin_config(channel, plugin_path):
    if 'plugins' not in channel:
        LogUtils.error("渠道SDK未配置可用插件")
        return 1
    root = ET.Element('plugins')
    for plugin in channel['plugins']:
        param_node = ET.SubElement(root, 'plugin')
        param_node.set('name', plugin['name'])
        param_node.set('type', plugin['type'])
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(plugin_path, xml_declaration=True, encoding='utf-8', method='xml')
    return 0


def exec_cmd(cmd):
    try:
        LogUtils.info('*********************cmd start***********************')
        cmd = cmd.replace('\\', '/')
        cmd = re.sub('/+', '/', cmd)
        st = subprocess.STARTUPINFO
        st.dwFlags = subprocess.STARTF_USESHOWWINDOW
        st.wShowWindow = subprocess.SW_HIDE
        LogUtils.info('cmd: %s', cmd)
        process = subprocess.Popen(cmd, shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        std, err = process.communicate()
        if process.returncode:
            LogUtils.error("\n" + err.decode('gbk'))
            LogUtils.info('===>exec Fail<===')
        else:
            # LogUtils.info(std.decode('gbk'))
            LogUtils.info('===>exec success<===')
        return process.returncode
    except Exception as e:
        LogUtils.error('Exception:' + e.__str__())
        return 1
    finally:
        LogUtils.info('*********************cmd end***********************')
        process.kill()


def exec_cmd2(cmd):
    try:
        LogUtils.info('*********************cmd start***********************')
        cmd = cmd.replace('\\', '/')
        cmd = re.sub('/+', '/', cmd)
        st = subprocess.STARTUPINFO
        st.dwFlags = subprocess.STARTF_USESHOWWINDOW
        st.wShowWindow = subprocess.SW_HIDE
        LogUtils.info('cmd: %s', cmd)
        process = subprocess.Popen(cmd, shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        std, err = process.communicate()
        if process.returncode:
            LogUtils.error("\n" + err.decode('gbk'))
            LogUtils.info('===>exec Fail<===')
            return None
        else:
            return std.decode('utf-8')
    except Exception as e:
        LogUtils.error('Exception:' + e.__str__())
        return None
    finally:
        LogUtils.info('*********************cmd end***********************')
        process.kill()
