import xml.dom.minidom
import os
import json

def find_keil_project_flie(keil_path, extension_name):
    if os.path.exists(keil_path):
        print("path exist, start find project file")
        print("file_path = " + keil_path)
    else:
        print("path is not exist")
        return []

    keil_file_list = []
    for root, dirs, files_list in os.walk(keil_path):
        for file in files_list:
            if file.endswith(extension_name):
                abs_file_path = keil_path+ "\\" +file
                if len(keil_file_list) == 0:
                    keil_file_list.append(abs_file_path)
                else:
                    if os.path.getmtime(abs_file_path) > os.path.getmtime(keil_file_list[0]):
                        keil_file_list.clear()
                        keil_file_list.append(abs_file_path)
    return keil_file_list[0]

def get_xml_info(file_path, TName):
    directory = os.getcwd()
    DomTree = xml.dom.minidom.parse(file_path)
    collection = DomTree.documentElement

    #get target list
    target_list = {}
    targets = collection.getElementsByTagName("Target")
    for target in targets:
        target_name = target.getElementsByTagName("TargetName")[0].firstChild.data
        target_list[target_name] = target
        print(target_list)

    #find target name
    if TName in target_list:
        target_handle = target_list[TName]
    else:
        print("find target name fial", target_list.keys())
        return []
    #获取c文件的define和include
    cads = target_handle.getElementsByTagName("Cads")[0]
    c_define = cads.getElementsByTagName("Define")[0].firstChild.data.split(",")
    c_incs   = cads.getElementsByTagName("IncludePath")[0].firstChild.data.split(';')
    c_incs_list = []
    for item in c_incs:
        if item.startswith('.'):
            item = item.split('.')[-1]
        if "\\" in item:
            item = item.replace('\\', '/')
        if item.startswith('/'):
            c_incs_list.append(item[1:])
        else:
            c_incs_list.append(item)

    #获取汇编文件的define和include
    aads = target_handle.getElementsByTagName("Aads")[0]
    a_define = aads.getElementsByTagName("Define")[0].firstChild.data.split(",")
    a_incs = aads.getElementsByTagName("IncludePath")[0].firstChild.data.split(';')
    a_incs_list = []
    for item in a_incs:
        if item.startswith('.'):
            item = item.split('.')[-1]
        if "\\" in item:
            item = item.replace('\\', '/')
        if item.startswith('/'):
            a_incs_list.append(item[1:])
        else:
            a_incs_list.append(item)

    ##综合c文件和汇编文件的define 和include
    define_list = []
    inc_list = []
    for item in c_define:
        if item not in define_list:
            define_list.append(item)
    for item in a_define:
        if item not in define_list:
            define_list.append(item)


    for item in c_incs_list:
        if item not in inc_list:
            inc_list.append(item)
    for item in a_incs_list:
        if item not in inc_list:
            inc_list.append(item)

    #获取文件信息
    file_list = []
    filesnodes = target_handle.getElementsByTagName("File")
    for filenode in filesnodes:
        cfilename = filenode.getElementsByTagName("FileName")[0].firstChild.data
        cfiletype = filenode.getElementsByTagName("FileType")[0].firstChild.data
        cfilepath = filenode.getElementsByTagName("FilePath")[0].firstChild.data
        cfilepath = '/' + cfilepath.replace('\\', '/').split('./')[-1]
        file_list.append({"filename":cfilename, "filetype":cfiletype, "filepath":cfilepath})
    commands = []
    for item in file_list:
        arguments = []
        arguments.append("clang",)
        arguments.append("-mcpu=cortex-m0")
        arguments.append("-Og")
        arguments.append("-std=c99")
        arguments.append("-D__packed=__attribute__((packed))")
        arguments.append("-D__weak=__attribute__((weak))")
        for define in define_list:
            arguments.append("-D"+define)
        for include in inc_list:
            arguments.append("-I"+include)
        arguments.append("-IC:/Keil_v5/ARM/ARMCC/include")
        arguments.append("-fdeclspec")
        file = item["filepath"]
        if file.startswith('/'):
            file = file[1:]
        arguments.append(file)

        arguments.append("-o")
        object = file.split('/')[-1].split('.')[0]
        arguments.append("Objects/"+object+".o")
        commands.append({"directory":directory, "arguments":arguments, "file":file})
    return commands

def write_json_file(commands = []):
    if len(commands) == 0:
        return False

    json_flie_path = os.getcwd() + "\\compile_commands.json"
    if os.path.exists(json_flie_path):
        json_file = open(json_flie_path, mode='w+')
    else:
        json_file = open(json_flie_path, mode='w')

    #for item in commands:
    #    commands_json = json.dump(item, json_file, indent= 4)
    json.dump(commands, json_file, indent=2)


    for item in commands:
        print(item)

if __name__ == '__main__':
    work_path = os.getcwd()
    work_path = os.path.abspath(os.path.join(work_path, "../"))
    os.chdir(work_path)
    #get keil project file path
    project_file = find_keil_project_flie(work_path, "uvprojx")
    print(project_file)
    commands = get_xml_info(project_file, "Target_Demo")
    write_json_file(commands)
