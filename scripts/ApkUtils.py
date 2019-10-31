# -*- coding: utf-8 -*-
import os
import shutil
import sys
import os.path
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement
from PIL import Image

from scripts import Utils, LogUtils

'''
打包apk工具类
'''
androidNS = 'http://schemas.android.com/apk/res/android'


def decompile_apk(apk_file, target_dir, frame_work_dir):
    java = Utils.get_full_path('tools/jdk/bin/java')
    apk_tool = Utils.get_full_path('tools/apktool.jar')
    os.makedirs(target_dir)
    os.makedirs(frame_work_dir)
    cmd = "%s -jar %s d %s -o %s -p %s -f" % (java, apk_tool, apk_file, target_dir, frame_work_dir)
    return Utils.exec_cmd(cmd)


def jar2dex(src_dir, dex_path):
    """
        compile jar files to dex.
    """
    dex_tool_path = Utils.get_full_path('tools/dx.jar')
    java = Utils.get_full_path('tools/jdk/bin/java')
    cmd = '%s -jar %s --dex --output %s' % (java, dex_tool_path, dex_path)

    for f in os.listdir(src_dir):
        if f.endswith('.jar'):
            cmd = cmd + ' ' + os.path.join(src_dir, f)

    for f in os.listdir(os.path.join(src_dir, 'libs')):
        if f.endswith('.jar'):
            cmd = cmd + ' ' + os.path.join(src_dir, 'libs', f)
    return Utils.exec_cmd(cmd)


def dex2smali(dex_file, target_dir, path):
    """
        Transfer the dex to smali.
    """
    if not os.path.exists(dex_file):
        LogUtils.error('the dexfile is not exists. path:%s', dex_file)
        return 1
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    smali_tool = Utils.get_full_path('tools/baksmali.jar')
    java = Utils.get_full_path('tools/jdk/bin/java')
    cmd = '%s -jar %s -o %s %s' % (java, smali_tool, target_dir, dex_file)
    return Utils.exec_cmd(cmd)


def merge_manifest(decompile_dir, sdk_dir):
    target_manifest = os.path.join(decompile_dir, 'AndroidManifest.xml')
    sdk_manifest = os.path.join(sdk_dir, 'SDKManifest.xml')
    if not os.path.exists(target_manifest) or not os.path.exists(sdk_manifest):
        LogUtils.error('the manifest file is not exists.\n targetManifest: %s\n sdkManifest: %s', target_manifest, sdk_manifest)
        return 1
    ET.register_namespace('android', androidNS)
    target_tree = ET.parse(target_manifest)
    target_root = target_tree.getroot()
    # 去除manifest标签中compileSdkVersion属性
    attrs = target_root.attrib
    target_root.attrib = {}
    for s in attrs:
        if s.find('compileSdkVersion') < 0:
            target_root.set(s, attrs[s])

    ET.register_namespace('android', androidNS)
    sdk_tree = ET.parse(sdk_manifest)
    sdk_root = sdk_tree.getroot()

    f = open(target_manifest)
    target_content = f.read()
    f.close()
    permission_config_node = sdk_root.find('permissionConfig')
    if permission_config_node is not None and len(permission_config_node) > 0:
        for child in list(permission_config_node):
            key = '{' + androidNS + '}name'
            val = child.get(key)
            if val is not None and len(val) > 0:
                if -1 == target_content.find(val):
                    target_root.append(child)

    app_config_node = sdk_root.find('applicationConfig')
    app_node = target_root.find('application')
    if app_config_node is not None:
        proxy_application_name = app_config_node.get('proxyApplication')
        if proxy_application_name is not None and len(proxy_application_name) > 0:
            meta_node = SubElement(app_node, 'meta-data')
            key = '{' + androidNS + '}name'
            val = '{' + androidNS + '}value'
            meta_node.set(key, 'SS_APPLICATION_PROXY_NAME')
            meta_node.set(val, proxy_application_name)
        for child in list(app_config_node):
            target_root.find('application').append(child)

    target_tree.write(target_manifest, xml_declaration=True, encoding='utf-8', method='xml')
    LogUtils.info('merge manifest file success.')
    return 0


def copy_libs(decompile_dir, sdk_dir):

    cpus = ['arm64-v8a', 'armeabi', 'armeabi-v7a', 'mips', 'mips64', 'x86', 'x86_64']
    dest_dir = os.path.join(decompile_dir, 'lib')
    src_dir = os.path.join(sdk_dir, 'libs')
    if not os.path.exists(src_dir):
        return
    if os.path.exists(dest_dir):
        for f in os.listdir(dest_dir):
            if f.endswith('.jar'):
                continue
            source_file = os.path.join(src_dir, f)
            target_file = os.path.join(dest_dir, f)
            if os.path.exists(source_file):
                Utils.copy_file(source_file, target_file)
    else:
        os.mkdir(dest_dir)
        for fi in os.listdir(src_dir):
            if fi.endswith('.jar'):
                continue
            source_file = os.path.join(src_dir, fi)
            target_file = os.path.join(dest_dir, fi)
            Utils.copy_file(source_file, target_file)


def copy_ext_res(game, decompile_dir):
    ext_res_path = 'games/' + game['id'] + '/ext'
    ext_res_path = Utils.get_full_path(ext_res_path)
    if os.path.exists(ext_res_path):
        LogUtils.warning('the game ext res path: %s', ext_res_path)
        Utils.copy_file(ext_res_path, decompile_dir)


def rename_package_name(decompile_dir, package_name):
    manifest_file = decompile_dir + '/AndroidManifest.xml'
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    old_package_name = root.attrib.get('package')

    if package_name is None or len(package_name) <= 0:
        return old_package_name

    if package_name[0:1] == '.':
        package_name = old_package_name + package_name
    LogUtils.info('renamePackageName ------------the new package name is %s', package_name)
    app_node = root.find('application')

    activity_list = app_node.findall('activity')
    key = '{' + androidNS + '}name'
    if activity_list is not None and len(activity_list) > 0:
        for aNode in activity_list:
            activity_name = aNode.attrib[key]
            if activity_name[0:1] == '.':
                activity_name = old_package_name + activity_name
            elif activity_name.find('.') == -1:
                activity_name = old_package_name + '.' + activity_name
            aNode.attrib[key] = activity_name

    service_list = app_node.findall('service')
    if service_list is not None and len(service_list) > 0:
        for sNode in service_list:
            service_name = sNode.attrib[key]
            if service_name[0:1] == '.':
                service_name = old_package_name + service_name
            elif service_name.find('.') == -1:
                service_name = old_package_name + '.' + service_name
            sNode.attrib[key] = service_name

    receiver_list = app_node.findall('receiver')
    if receiver_list is not None and len(receiver_list) > 0:
        for sNode in receiver_list:
            receiver_name = sNode.attrib[key]
            if receiver_name[0:1] == '.':
                receiver_name = old_package_name + receiver_name
            elif receiver_name.find('.') == -1:
                receiver_name = old_package_name + '.' + receiver_name
            sNode.attrib[key] = receiver_name

    provider_list = app_node.findall('provider')
    if provider_list is not None and len(provider_list) > 0:
        for sNode in provider_list:
            provider_name = sNode.attrib[key]
            if provider_name[0:1] == '.':
                provider_name = old_package_name + provider_name
            elif provider_name.find('.') == -1:
                provider_name = old_package_name + '.' + provider_name
            sNode.attrib[key] = provider_name

            provider_authorities = sNode.attrib['{' + androidNS + '}authorities']
            if provider_authorities.find(old_package_name) != -1:
                provider_authorities = provider_authorities.replace(old_package_name, package_name)
                sNode.attrib['{' + androidNS + '}authorities'] = provider_authorities

    root.attrib['package'] = package_name
    tree.write(manifest_file, xml_declaration=True, encoding='utf-8', method='xml')
    return package_name


def write_develop_info(game, channel, decompile_dir):
    assets_path = os.path.join(decompile_dir, 'assets')
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)
    develop_config_file = os.path.join(assets_path, 'developer_configs_ss.properties')
    ret = Utils.write_developer_properties(game, channel, develop_config_file)
    if ret:
        return ret
    plugin_file = os.path.join(assets_path, 'plugin_configs_ss.xml')
    return Utils.write_plugin_config(channel, plugin_file)


def do_sdk_script(channel, decompile_dir, package_name, sdk_dir):
    script = os.path.join(sdk_dir, 'script.pyc')
    if not os.path.exists(script):
        return 0
    try:
        sys.path.append(sdk_dir)
        import script
        script.execute(channel, decompile_dir, package_name)
        del sys.modules['script']
        sys.path.remove(sdk_dir)
        return 0
    except Exception as e:
        LogUtils.error('%s execute failed:%s', script, e.__str__())
        return 1


def modify_manifest(channel, decompile_dir, package_name):
    manifest_file = decompile_dir + '/AndroidManifest.xml'
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    app_node = root.find('application')
    # 修改游戏名称
    if len(channel['gameName']) > 0:
        app_node.set('{' + androidNS + '}label', channel['gameName'])
        activity_node_lst = app_node.findall('activity')
        for activity_node in activity_node_lst:
            if activity_node.get('{' + androidNS + '}label') is not None:
                activity_node.set('{' + androidNS + '}label', channel['gameName'])
        LogUtils.info('modify game name: %s', channel['gameName'])
    # 写入meta-data
    key = '{' + androidNS + '}name'
    val = '{' + androidNS + '}value'
    meta_data_list = app_node.findall('meta-data')
    if meta_data_list is not None:
        for metaDataNode in meta_data_list:
            key_name = metaDataNode.attrib[key]
            for child in channel['sdkParams']:
                if key_name == child['name'] and child['writeIn'] == '1':
                    LogUtils.warning('the meta-data node %s repeated. remove it .', key_name)
                    app_node.remove(metaDataNode)
    for child in channel['sdkParams']:
        if child['writeIn'] is not None and child['writeIn'] == '1':
            meta_node = SubElement(app_node, 'meta-data')
            meta_node.set(key, child['name'])
            meta_node.set(val, child['value'])
            LogUtils.info('writeIn meta-data: %s=%s', child['name'], child['value'])
    # 修改替换包名占位符
    xml_str = ET.tostring(root, 'utf-8').decode('utf-8')
    if xml_str.find('NEW_PACKAGE_NAME') != -1:
        LogUtils.info('modify package name: %s', package_name)
        xml_str = xml_str.replace('NEW_PACKAGE_NAME', package_name)
        root = ET.fromstring(xml_str)

    Utils.indent(root)
    tree = ET.ElementTree(root)
    tree.write(manifest_file, xml_declaration=True, encoding='utf-8', method='xml')
    LogUtils.info('The manifestFile modify successfully')


def generate_r_file(package_name, decompile_dir):
    # check_value_resources(decompile_dir)
    temp_path = os.path.dirname(decompile_dir) + '/temp'
    LogUtils.debug('generate R:the temp path is %s', temp_path)
    if os.path.exists(temp_path):
        Utils.del_file(temp_path)
    os.makedirs(temp_path)
    res_path = decompile_dir + '/res'
    temp_res_path = temp_path + '/res'
    Utils.copy_file(res_path, temp_res_path)
    gen_path = temp_path + '/gen'
    os.makedirs(gen_path)

    aapt_path = Utils.get_full_path('tools/aapt2.exe')
    android_path = Utils.get_full_path('tools/android.jar')
    java = Utils.get_full_path('tools/jdk/bin/java')
    javac = Utils.get_full_path('tools/jdk/bin/javac')

    manifest_path = decompile_dir + '/AndroidManifest.xml'
    res_flat_path = temp_path + "/res_flat.zip"
    cmd = '%s compile -o %s --dir %s' % (aapt_path, res_flat_path, temp_res_path)
    ret = Utils.exec_cmd(cmd)
    if ret:
        return 1
    cmd = '%s link -o %s --manifest %s -I %s --java %s %s' % (aapt_path, temp_path+'/res.apk', manifest_path, android_path, gen_path, res_flat_path)
    ret = Utils.exec_cmd(cmd)
    if ret:
        return 1

    LogUtils.info('package_name:%s', package_name)
    r_path = package_name.replace('.', '/')
    r_path = gen_path + '/' + r_path + '/R.java'
    cmd = '%s -source 1.8 -target 1.8 -encoding UTF-8 %s' % (javac, r_path)
    ret = Utils.exec_cmd(cmd)
    if ret:
        return 1
    dex_path = temp_path + '/classes.dex'
    dex_tool_path = Utils.get_full_path('tools/dx.jar')
    cmd = '%s -jar %s --dex --output %s %s' % (java, dex_tool_path, dex_path, gen_path)
    ret = Utils.exec_cmd(cmd)
    if ret:
        return 1
    smali_path = decompile_dir + '/smali'
    ret = dex2smali(dex_path, smali_path, '')
    if ret:
        return 1
    return 0


def classes_split(decompile_dir, sdk_dest_dir):
    smali_path = decompile_dir + '/smali'
    filter_path = sdk_dest_dir + '/classes.filter'
    if not os.path.exists(filter_path):
        return 0
    filter_file = open(filter_path, encoding='utf-8')
    content = filter_file.read()
    filter_file.close()
    smali2_path = decompile_dir + '/smali_classes2'
    if not os.path.exists(smali2_path):
        os.mkdir(smali2_path)
    try:
        filters = eval(content)
        for dir in filters:
            class_src_dir = smali_path + '/' + dir
            if os.path.exists(class_src_dir):
                class_dest_dir = smali2_path + '/' + dir
                shutil.move(class_src_dir, class_dest_dir)
        return 0
    except Exception as e:
        LogUtils.error('%s parse failed: %s', filter_path, e.__str__())
        return 1


def edit_yml(channel, decompile_dir):
    LogUtils.info('-----> EditYML <------')
    path = decompile_dir + '/apktool.yml'
    yml_file = open(path, encoding='utf-8')
    content = ''
    while True:
        line = yml_file.readline()
        if line.find('- assets/') == 0:
            yml_file.tell()
        elif line.find('targetSdkVersion') != -1:
            config = Utils.get_local_config()
            if config is not None and config['TARGET_SDK_VERSION'] != '0':
                content += '  targetSdkVersion: \'' + config['TARGET_SDK_VERSION'] + '\'\n'
            else:
                content += line
        elif line.find('versionCode') != -1 and len(channel['gameVersionCode']) > 0:
            content += '  versionCode: \'' + channel['gameVersionCode'] + '\'\n'
        elif line.find('versionName') != -1 and len(channel['gameVersionName']) > 0:
            content += '  versionName: ' + channel['gameVersionName'] + '\n'
        else:
            if not line:
                break
            line.replace('\r', '')
            if line.strip() != '':
                content += line
                if line.find('doNotCompress:') == 0:
                    yml_file.tell()
                    content += '- assets/*\n'
    LogUtils.info("apktool.yml:\n%s", content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def recompile_apk(source_folder, apk_file, frame_work_dir):
    java = Utils.get_full_path('tools/jdk/bin/java')
    apk_tool = Utils.get_full_path('tools/apktool.jar')
    cmd = "%s -jar %s b %s -o %s -p %s" % (java, apk_tool, source_folder, apk_file, frame_work_dir)
    return Utils.exec_cmd(cmd)


def copy_root_ext_files(apk_file, decompile_dir):
    aapt = Utils.get_full_path('tools/aapt2.exe')
    ignore_files = ['AndroidManifest.xml', 'apktool.yml', 'smali', 'res', 'original', 'lib', 'build', 'assets',
                    'unknown', 'kotlin', 'smali_classes2', 'smali_classes3', 'smali_classes4', 'smali_classes5']
    ignore_file_paths = []
    for file in ignore_files:
        path = os.path.join(decompile_dir, file)
        ignore_file_paths.append(path)

    add_files = []
    add_files = Utils.list_files(decompile_dir, add_files, ignore_file_paths)
    if len(add_files) <= 0:
        return 0
    cmd = '%s add %s'
    for f in add_files:
        name = f[len(decompile_dir) + 1:]
        cmd = cmd + ' ' + name
    cmd = cmd % (aapt, apk_file)
    curr_path = os.getcwd()
    os.chdir(decompile_dir)
    ret = Utils.exec_cmd(cmd)
    os.chdir(curr_path)
    return ret


def sign_apk(game, apk_file):
    key_path = Utils.get_full_path('games/' + game['id'] + '/keystore/' + game['keystore'])
    if not os.path.exists(key_path):
        LogUtils.info('the keystore file not exists: %s', key_path)
        return 1
    LogUtils.info('the keystore file is %s', key_path)
    aapt = Utils.get_full_path('tools/aapt.exe')
    lcmd = "%s list %s" % (aapt, apk_file)
    out = Utils.exec_cmd2(lcmd)
    if out is not None and len(out) > 0:
        for filename in out.split('\n'):
            if filename.find('META-INF') == 0:
                rmcmd = "%s remove %s %s" % (aapt, apk_file, filename)
                Utils.exec_cmd(rmcmd)
    jar_signer = Utils.get_full_path('tools/jdk/bin/jarsigner')
    sign_cmd = "%s -keystore %s -storepass %s -keypass %s %s %s -sigalg  SHA1withRSA -digestalg SHA1" % (jar_signer,
                                                                                                         key_path,
                                                                                                         game['keypwd'],
                                                                                                         game['aliaspwd'],
                                                                                                         apk_file,
                                                                                                         game['alias'])
    return Utils.exec_cmd(sign_cmd)


def align_apk(apk_file, target_file):
    align = Utils.get_full_path('tools/zipalign.exe')
    cmd = '%s -f 4 %s %s' % (align, apk_file, target_file)
    return Utils.exec_cmd(cmd)


def append_channel_mark(game, sdk_dest_dir, decompile_dir):
    game_icon_path = 'games/' + game['id'] + '/icon/icon.png'
    game_icon_path = Utils.get_full_path(game_icon_path)
    if not os.path.exists(game_icon_path):
        LogUtils.info('The game %s icon is not exists : %s', game['id'], game_icon_path)
        return
    LogUtils.info('The game %s icon path : %s', game['id'], game_icon_path)

    game_icon_name = get_app_icon_name(decompile_dir)
    if game_icon_name is None:
        return
    game_icon_name = game_icon_name + '.png'
    LogUtils.info('The game icon name: %s', game_icon_name)

    icon_img = Image.open(game_icon_path)
    mark_path = sdk_dest_dir + '/mark.png'
    if not os.path.exists(mark_path):
        LogUtils.info('The mark path is not exists : %s', mark_path)
    else:
        LogUtils.info('The mark path : %s', mark_path)
        mark_img = Image.open(mark_path)
        icon_img = merge_icon_mark(icon_img, mark_img, (0, 0))

    ldpi_icon = icon_img.resize((36, 36), Image.ANTIALIAS)
    mdpi_icon = icon_img.resize((48, 48), Image.ANTIALIAS)
    hdpi_icon = icon_img.resize((72, 72), Image.ANTIALIAS)
    xhdpi_icon = icon_img.resize((96, 96), Image.ANTIALIAS)
    xxhdpi_icon = icon_img.resize((144, 144), Image.ANTIALIAS)
    xxxhdpi_icon = icon_img.resize((192, 192), Image.ANTIALIAS)
    icons = (ldpi_icon, mdpi_icon, hdpi_icon, xhdpi_icon, xxhdpi_icon, xxxhdpi_icon)

    drawables = ('drawable-ldpi', 'drawable-mdpi', 'drawable-hdpi', 'drawable-xhdpi', 'drawable-xxhdpi', 'drawable-xxxhdpi')
    mipmaps = ('mipmap-ldpi', 'mipmap-mdpi', 'mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi')
    for drawable in drawables:
        icon_dir = decompile_dir + '/res/' + drawable
        Utils.del_file(icon_dir + '/' + game_icon_name)
        if os.path.exists(icon_dir) and len(os.listdir(icon_dir)) <= 0:
            os.rmdir(icon_dir)

        icon_dir = decompile_dir + '/res/' + drawable + '-v4'
        Utils.del_file(icon_dir + '/' + game_icon_name)
        if os.path.exists(icon_dir) and len(os.listdir(icon_dir)) <= 0:
            os.rmdir(icon_dir)
    if not os.path.exists(decompile_dir + '/res/drawable'):
        os.mkdir(decompile_dir + '/res/drawable')
    xxhdpi_icon.save(decompile_dir + '/res/drawable/' + game_icon_name, 'PNG')

    for i in range(len(mipmaps)):
        icon_dir = decompile_dir + '/res/' + mipmaps[i] + '-v4'
        Utils.del_file(icon_dir + '/' + game_icon_name)
        if os.path.exists(icon_dir) and len(os.listdir(icon_dir)) <= 0:
            os.rmdir(icon_dir)

        icon_dir = decompile_dir + '/res/' + mipmaps[i]
        if not os.path.exists(icon_dir):
            os.makedirs(icon_dir)
        icons[i].save(os.path.join(icon_dir, game_icon_name), 'PNG')


# 从AndroidManifest.xml中获取游戏图标的名称
def get_app_icon_name(decompile_dir):
    try:
        ET.register_namespace('android', androidNS)
        tree = ET.parse(decompile_dir + '/AndroidManifest.xml')
        root = tree.getroot()
        application = root.find('application')
        key = '{' + androidNS + '}icon'
        icon_name = application.get(key)
        LogUtils.info('=>AndroidManifest key iconName: %s', icon_name)
        if icon_name is None:
            name = 'ic_launcher'
        else:
            name = icon_name.split('/')[-1]
        application.set(key, '@mipmap/' + name)
        tree.write(decompile_dir + '/AndroidManifest.xml', xml_declaration=True, encoding='utf-8', method='xml')
        return name
    except Exception as e:
        LogUtils.error("get_app_icon_name exception")
        LogUtils.error('parse xml exception!\n%s', e.__str__())
        return None


def merge_icon_mark(img_icon, img_mark, position):
    if img_icon.mode != 'RGBA':
        img_icon = img_icon.convert('RGBA')
    mark_layer = Image.new('RGBA', img_icon.size, (0, 0, 0, 0))
    mark_layer.paste(img_mark, position)
    return Image.composite(mark_layer, img_icon, mark_layer)


def check_value_resources(decompileDir):
    values = ['strings.xml', 'styles.xml', 'colors.xml', 'dimens.xml', 'ids.xml', 'attrs.xml', 'integers.xml',
              'arrays.xml', 'bools.xml', 'drawables.xml', 'public.xml']
    values_dir = decompileDir + '/res/values'
    exists_strs = {}
    strings = values_dir + '/strings.xml'
    if os.path.exists(strings):
        string_tree = ET.parse(strings)
        root = string_tree.getroot()
        for node in list(root):
            string = {}
            name = node.attrib.get('name')
            val = node.text
            string['file'] = strings
            string['name'] = name
            string['value'] = val
            exists_strs[name] = string

    exists_colors = {}
    colors = values_dir + 'colors.xml'
    if os.path.exists(colors):
        color_tree = ET.parse(colors)
        root = color_tree.getroot()
        for node in list(root):
            color = {}
            color['file'] = colors
            color['name'] = node.attrib.get('name')
            color['value'] = node.text.lower()
            exists_colors[name] = color

    value_files = {}
    for filename in os.listdir(values_dir):
        if filename in values:
            continue
        src_file = values_dir + '/' + filename
        if os.path.splitext(src_file)[1] != '.xml':
            continue
        tree = ET.parse(src_file)
        root = tree.getroot()
        if root.tag != 'resources':
            continue
        for node in list(root):
            if node.tag == 'string':
                dict_res = exists_strs
            elif node.tag == 'color':
                dict_res = exists_colors
            else:
                continue
            res = dict_res.get(node.attrib.get('name'))
            if res is not None:
                root.remove(node)
            else:
                value = {}
                value['file'] = src_file
                value['name'] = node.attrib.get('name')
                value['value'] = node.text
                dict_res[name] = value

        value_files[src_file] = tree

    for valFile in value_files.keys():
        value_files[valFile].write(valFile, 'UTF-8')
