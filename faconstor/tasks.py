from __future__ import absolute_import
from logging import log
from celery import shared_task
import datetime
import time
import paramiko
import os
import json
import subprocess
import logging
import uuid
import re
from lxml import etree

from django.db import connection
from django.db.models import Q

from faconstor.models import *
from . import remote
from .models import *
from TSDRM import settings
from .api import SQLApi
from .CVApi import *

logger = logging.getLogger('tasks')


@shared_task
def get_disk_space_crond():
    """
    一周获取一次Commvault磁盘信息
        工具ID MediaID 可用容量、保留空间、总容量、取数时间
        
    """
    from .views import get_credit_info
    commvaul_utils = UtilsManage.objects.exclude(state="9").filter(util_type="Commvault")
    point_tag = uuid.uuid1()
    for cu in commvaul_utils:
        _, sqlserver_credit = get_credit_info(cu.content)
        dm = SQLApi.CVApi(sqlserver_credit)
        disk_space = dm.get_library_space_info()

        for ds in disk_space:
            disk_space_save_data = dict()
            disk_space_save_data["utils_id"] = cu.id
            disk_space_save_data["media_id"] = int(ds["MediaID"]) if ds["MediaID"] else 0
            disk_space_save_data["capacity_avaible"] = int(ds["CapacityAvailable"]) if ds["CapacityAvailable"] else 0
            disk_space_save_data["space_reserved"] = int(ds["SpaceReserved"]) if ds["SpaceReserved"] else 0
            disk_space_save_data["total_space"] = int(ds["TotalSpaceMB"]) if ds["TotalSpaceMB"] else 0
            disk_space_save_data["extract_time"] = datetime.datetime.now()
            disk_space_save_data["point_tag"] = point_tag
            try:
                DiskSpaceWeeklyData.objects.create(**disk_space_save_data)
            except Exception as e:
                print(e)


# @shared_task(bind=True, default_retry_delay=300, max_retries=5)  # 错误处理机制，因网络延迟等问题的重试；
@shared_task
def exec_script(steprunid, username, fullname):
    """
    执行当前步骤在指定系统下的所有脚本
    """
    end_step_tag = True
    steprun = StepRun.objects.filter(id=steprunid)
    steprun = steprun[0]
    scriptruns = steprun.scriptrun_set.exclude(Q(state__in=("9", "DONE", "IGNORE")) | Q(result=0))
    for script_run in scriptruns:
        script_instance = script_run.script_instance
        script = script_instance.script
        script_run.starttime = datetime.datetime.now()
        script_run.result = ""
        script_run.state = "RUN"
        script_run.save()
        # 执行脚本内容
        # cmd = r"{0}".format(script.script.scriptpath + script.script.filename)
        cmd = r"{0}".format(script.script_text)

        # HostsManage
        cur_host_manage = script_instance.hosts_manage
        ip = cur_host_manage.host_ip
        username = cur_host_manage.username
        password = cur_host_manage.password
        script_type = cur_host_manage.type

        system_tag = ""
        if script_type == "SSH":
            system_tag = "Linux"
        if script_type == "BAT":
            system_tag = "Windows"
        rm_obj = remote.ServerByPara(cmd, ip, username, password, system_tag)  # 服务器系统从视图中传入
        result = rm_obj.run(script.succeedtext)

        script_run.endtime = datetime.datetime.now()
        script_run.result = result["exec_tag"]
        script_run.explain = result['data']

        # 处理脚本执行失败问题
        if result["exec_tag"] == 1:
            script_run.runlog = result['log']
            script_run.explain = result['data']

            end_step_tag = False
            script_run.state = "ERROR"
            steprun.state = "ERROR"
            script_run.save()
            steprun.save()
            break
        script_run.state = "DONE"
        script_run.save()

    if end_step_tag:
        steprun.state = "DONE"
        steprun.save()

        task = steprun.processtask_set.filter(state="0")
        if len(task) > 0:
            task[0].endtime = datetime.datetime.now()
            task[0].state = "1"
            task[0].operator = username
            task[0].save()

            nextstep = steprun.step.next.exclude(state="9")
            if len(nextstep) > 0:
                nextsteprun = nextstep[0].steprun_set.exclude(state="9").filter(processrun=steprun.processrun)
                if len(nextsteprun) > 0:
                    mysteprun = nextsteprun[0]
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = steprun.processrun
                    myprocesstask.steprun = mysteprun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = username
                    myprocesstask.receiveuser = username
                    myprocesstask.type = "RUN"
                    myprocesstask.state = "0"
                    myprocesstask.content = steprun.processrun.DataSet.clientName + "的" + steprun.processrun.process.name + "流程进行到“" + \
                                            nextstep[
                                                0].name + "”，请" + fullname + "处理。"
                    myprocesstask.save()


def content_load_params(script_instance):
    """
    脚本中传入参数
    :return:
    """
    params = eval(script_instance.params)
    script = script_instance.script
    script_text = script.script_text
    # 匹配出参数，替换
    def get_variable_name(content, param_type):
        variable_list = []
        variable_list_with_symbol = []
        com = ""
        com_with_symbol = ""
        if param_type == "HOST":
            com = re.compile("\(\((.*?)\)\)")
            com_with_symbol = re.compile("(\(\(.*?\)\))")
        if param_type == "PROCESS":
            com = re.compile("\{\{(.*?)\}\}")
            com_with_symbol = re.compile("(\{\{.*?\}\})")
        if param_type == "SCRIPT":
            com = re.compile("\[\[(.*?)\]\]")
            com_with_symbol = re.compile("(\[\[.*?\]\])")
        if com:
            variable_list = com.findall(content)
        if com_with_symbol:
            variable_list_with_symbol = com_with_symbol.findall(content)
        return variable_list, variable_list_with_symbol

    def get_value_from_params(variable_name, params):
        param_value = ""
        for param in params:
            if variable_name.strip() == param["variable_name"]:
                param_value = param["param_value"]
                break
        return param_value

    # 流程参数参数 注意空格
    process_variable_list, process_variable_list_with_symbol = get_variable_name(script_text, "PROCESS")
    for n, pv in enumerate(process_variable_list):
        param_value = get_value_from_params(pv, params)
        script_text = script_text.replace(process_variable_list_with_symbol[n], param_value)

    # 主机参数
    host_variable_list, host_variable_list_with_symbol = get_variable_name(script_text, "HOST")
    for n, hv in enumerate(host_variable_list):
        param_value = get_value_from_params(hv, params)
        script_text = script_text.replace(host_variable_list_with_symbol[n], param_value)
    # 脚本参数
    script_variable_list, script_variable_list_with_symbol = get_variable_name(script_text, "SCRIPT")
    for n, sv in enumerate(script_variable_list):
        param_value = get_value_from_params(sv, params)
        script_text = script_text.replace(script_variable_list_with_symbol[n], param_value)

    return script_text


@shared_task
def force_exec_script(processrunid):
    try:
        processrunid = int(processrunid)
    except ValueError as e:
        print("网络异常导致流程ID未传入, ", e)
    else:
        try:
            processrun = ProcessRun.objects.get(id=processrunid)
        except ProcessRun.DoesNotExist as e:
            print("流程不存在, ", e)
        else:
            all_step_runs = processrun.steprun_set.exclude(step__state="9").filter(step__force_exec=1)
            for steprun in all_step_runs:
                cur_step_scripts = steprun.scriptrun_set.all()
                for script_run in cur_step_scripts:
                    script_instance = script_run.script
                    script = script_instance.script
                    script_name = script_instance.name if script_instance.name else ""
                    
                    script_run.starttime = datetime.datetime.now()
                    script_run.result = ""
                    script_run.state = "RUN"
                    script_run.save()

                    # HostsManage
                    cur_host_manage = script_instance.hosts_manage
                    ip = cur_host_manage.host_ip
                    username = cur_host_manage.username
                    password = cur_host_manage.password
                    system_tag = cur_host_manage.os

                    if system_tag == "Linux":
                        ###########################
                        # 创建linux下目录:         #
                        #   mkdir path -p 覆盖路径 #
                        ###########################
                        linux_temp_script_path = "/tmp/drm/{processrunid}".format(**{"processrunid": processrun.id})
                        mkdir_cmd = "mkdir {linux_temp_script_path} -p".format(
                            **{"linux_temp_script_path": linux_temp_script_path})
                        mkdir_obj = remote.ServerByPara(mkdir_cmd, ip, username, password, system_tag)
                        mkdir_result = mkdir_obj.run("")

                        linux_temp_script_name = "tmp_script_{scriptrun_id}.sh".format(**{"scriptrun_id": script_run.id})
                        linux_temp_script_file = linux_temp_script_path + "/" + linux_temp_script_name

                        # 写入本地文件
                        script_path = os.path.join(
                            os.path.join(
                                os.path.join(settings.BASE_DIR, "faconstor"), 
                                "upload"
                            ),
                            "script"
                        )

                        local_file = script_path + os.sep + "{0}_local_script.sh".format(processrun.process.name)

                        try:
                            # 处理脚本内容
                            script_text = content_load_params(script_instance)
                            with open(local_file, "w") as f:
                                f.write(script_text)
                        except FileNotFoundError as e:
                            script_run.runlog = "Linux脚本写入本地失败。"  # 写入错误类型
                            script_run.explain = "Linux脚本写入本地失败：{0}。".format(e)
                            script_run.state = "ERROR"
                            script_run.save()
                            steprun.state = "ERROR"
                            steprun.save()
                        else:
                            # 上传Linux服务器
                            try:
                                ssh = paramiko.Transport((ip, 22))
                                ssh.connect(username=username, password=password)
                                sftp = paramiko.SFTPClient.from_transport(ssh)
                            except paramiko.ssh_exception.SSHException as e:
                                script_run.runlog = "连接服务器失败。"  # 写入错误类型
                                script_run.explain = "连接服务器失败：{0}。".format(e)  # 写入错误类型
                                script_run.state = "ERROR"
                                script_run.save()
                                steprun.state = "ERROR"
                                steprun.save()
                            else:
                                try:
                                    sftp.put(local_file, linux_temp_script_file)
                                except FileNotFoundError as e:
                                    script_run.runlog = "上传linux脚本文件失败。"  # 写入错误类型
                                    script_run.explain = "上传linux脚本文件失败：{0}。".format(e)  # 写入错误类型
                                    script_run.state = "ERROR"
                                    script_run.save()
                                    steprun.state = "ERROR"
                                    steprun.save()
                                else:
                                    sftp.chmod(linux_temp_script_file, int("755", 8))

                                ssh.close()

                            # 执行脚本(上传文件(dos格式>>shell))
                            exe_cmd = r"sed -i 's/\r$//' {0}&&{0}".format(linux_temp_script_file)
                    else:
                        ############################
                        # 创建windows下目录:       #
                        #   先判断文件是否存在，再  #
                        #   mkdir/md path 创建文件 #
                        ############################
                        windows_temp_script_path = r"C:\drm\{processrunid}".format(**{"processrunid": processrun.id})
                        mkdir_cmd = "if not exist {windows_temp_script_path} mkdir {windows_temp_script_path}".format(
                            **{"windows_temp_script_path": windows_temp_script_path})
                        mkdir_obj = remote.ServerByPara(mkdir_cmd, ip, username, password, system_tag)
                        mkdir_result = mkdir_obj.run("")

                        windows_temp_script_name = "tmp_script_{scriptrun_id}.bat".format(**{"scriptrun_id": script_run.id})
                        windows_temp_script_file = windows_temp_script_path + r"\\" + windows_temp_script_name

                        # 处理脚本内容
                        script_text = content_load_params(script_instance)

                        para_list = script_text.split("\n")
                        for num, content in enumerate(para_list):
                            tmp_cmd = ""
                            if num == 0:
                                tmp_cmd = r"""echo {0}>{1}""".format(content, windows_temp_script_file)
                            else:
                                tmp_cmd = r"""echo {0}>>{1}""".format(content, windows_temp_script_file)

                            tmp_obj = remote.ServerByPara(tmp_cmd, ip, username, password, system_tag)
                            tmp_result = tmp_obj.run("")

                            if tmp_result["exec_tag"] == 1:
                                script_run.runlog = "上传windows脚本文件失败。"  # 写入错误类型
                                script_run.explain = "上传windows脚本文件失败：{0}。".format(tmp_result["data"])
                                script_run.state = "ERROR"
                                script_run.save()
                                steprun.state = "ERROR"
                                steprun.save()

                        exe_cmd = windows_temp_script_file

                    # 执行文件
                    rm_obj = remote.ServerByPara(exe_cmd, ip, username, password, system_tag)
                    result = rm_obj.run(script.succeedtext)

                    script_run.endtime = datetime.datetime.now()
                    script_run.result = result['exec_tag']
                    script_run.explain = result['data']

                    # 处理脚本执行失败问题
                    if result["exec_tag"] == 1:
                        script_run.runlog = result['log']  # 写入错误类型
                        script_run.explain = result['data']
                        print("当前脚本执行失败,结束任务!")
                        script_run.state = "ERROR"
                        script_run.save()
                        steprun.state = "ERROR"
                        steprun.save()
                    else:
                        script_run.endtime = datetime.datetime.now()
                        script_run.state = "DONE"
                        script_run.save()

                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = steprun.processrun
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = steprun.processrun.creatuser
                        myprocesstask.type = "INFO"
                        myprocesstask.logtype = "SCRIPT"
                        myprocesstask.state = "1"
                        myprocesstask.content = "脚本" + script_name + "完成。"
                        myprocesstask.save()


def runstep(steprun, if_repeat=False, processrun_params={}):
    """
    执行当前步骤下的所有脚本
    返回值0,：错误，1：完成，2：确认，3：流程已结束
    if_repeat用于避免已执行步骤重复执行。
    """
    pri = processrun_params.get("pri", None)
    pri_id = processrun_params.get("pri_id", None)
    std_id = processrun_params.get("std_id", None)
    utils_content = processrun_params.get("utils_content", "")
    instance_name = pri.instanceName if pri else ""
    
    # 判断该步骤是否已完成，如果未完成，先执行当前步骤
    processrun = ProcessRun.objects.filter(id=steprun.processrun.id)
    processrun = processrun[0]
    if processrun.state == "RUN" or processrun.state == "ERROR":
        # 将错误流程改成RUN
        processrun.state = "RUN"
        processrun.save()

        if steprun.state != "DONE":
            # 判断是否有子步骤，如果有，先执行子步骤
            # 取消错误消息展示
            all_done_tasks = ProcessTask.objects.exclude(state="1").filter(processrun_id=processrun.id,
                                                                           type="ERROR")
            for task in all_done_tasks:
                task.state = "1"
                task.save()

            if not if_repeat:
                steprun.starttime = datetime.datetime.now()  # 这个位置pnode的starttime存多次
            steprun.state = "RUN"
            steprun.save()

            children = steprun.step.children.order_by("sort").exclude(state="9")
            if len(children) > 0:
                for child in children:
                    childsteprun = child.steprun_set.exclude(state="9").filter(processrun=steprun.processrun)
                    if len(childsteprun) > 0:
                        childsteprun = childsteprun[0]
                        start_time = childsteprun.starttime
                        if start_time:
                            if_repeat = True
                        else:
                            if_repeat = False
                        childreturn = runstep(childsteprun, if_repeat, processrun_params)
                        if childreturn == 0:
                            return 0
                        if childreturn == 2:
                            return 2
            scriptruns = steprun.scriptrun_set.exclude(Q(state__in=("9", "DONE", "IGNORE")) | Q(result=0))
            for scriptrun in scriptruns:
                # 目的：不在服务器存放脚本；
                #   Linux：通过ssh上传文件至服务器端；执行脚本；删除脚本；
                #   Windows：通过>/>> 逐行重定向字符串至服务端文件；执行脚本；删除脚本；

                scriptrun.starttime = datetime.datetime.now()
                scriptrun.result = ""
                scriptrun.state = "RUN"
                scriptrun.save()

                script_instance = scriptrun.script
                script = script_instance.script
                origin = script_instance.origin
                script_name = script_instance.name if script_instance.name else ""
                recover_job_id = ""
                if script.interface_type in ["Linux", "Windows"]:
                    # HostsManage
                    cur_host_manage = script_instance.hosts_manage
                    ip = cur_host_manage.host_ip
                    username = cur_host_manage.username
                    password = cur_host_manage.password

                    system_tag = script.interface_type
                    # linux_temp_script_file = "/tmp/tmp_script.sh"
                    # windows_temp_script_file = "C:/tmp_script.bat"

                    if system_tag == "Linux":
                        ###########################
                        # 创建linux下目录:         #
                        #   mkdir path -p 覆盖路径 #
                        ###########################
                        linux_temp_script_path = "/tmp/drm/{processrunid}".format(**{"processrunid": processrun.id})
                        mkdir_cmd = "mkdir {linux_temp_script_path} -p".format(
                            **{"linux_temp_script_path": linux_temp_script_path})
                        mkdir_obj = remote.ServerByPara(mkdir_cmd, ip, username, password, system_tag)
                        mkdir_result = mkdir_obj.run("")

                        linux_temp_script_name = "tmp_script_{scriptrun_id}.sh".format(**{"scriptrun_id": scriptrun.id})
                        linux_temp_script_file = linux_temp_script_path + "/" + linux_temp_script_name

                        # 写入本地文件
                        script_path = os.path.join(
                            os.path.join(
                                os.path.join(settings.BASE_DIR, "faconstor"), 
                                "upload"
                            ),
                            "script"
                        )

                        local_file = script_path + os.sep + "{0}_local_script.sh".format(processrun.process.name)

                        try:
                            with open(local_file, "w") as f:
                                # 处理脚本内容
                                script_text = content_load_params(script_instance)  # 待修改
                                f.write(script_text)
                        except FileNotFoundError as e:
                            scriptrun.runlog = "Linux脚本写入本地失败。"  # 写入错误类型
                            scriptrun.explain = "Linux脚本写入本地失败：{0}。".format(e)
                            scriptrun.state = "ERROR"
                            scriptrun.save()
                            scriptrun.state = "ERROR"
                            scriptrun.save()

                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = steprun.processrun
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = steprun.processrun.creatuser
                            myprocesstask.receiveauth = steprun.step.group
                            myprocesstask.type = "ERROR"
                            myprocesstask.state = "0"
                            myprocesstask.content = "Linux脚本" + script_name + "内容写入失败，请处理。"
                            myprocesstask.steprun_id = steprun.id
                            myprocesstask.save()
                            return 0

                        # 上传Linux服务器
                        try:
                            ssh = paramiko.Transport((ip, 22))
                            ssh.connect(username=username, password=password)
                            sftp = paramiko.SFTPClient.from_transport(ssh)
                        except paramiko.ssh_exception.SSHException as e:
                            scriptrun.runlog = "连接服务器失败。"  # 写入错误类型
                            scriptrun.explain = "连接服务器失败：{0}。".format(e)  # 写入错误类型
                            scriptrun.state = "ERROR"
                            scriptrun.save()
                            steprun.state = "ERROR"
                            steprun.save()

                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = steprun.processrun
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = steprun.processrun.creatuser
                            myprocesstask.receiveauth = steprun.step.group
                            myprocesstask.type = "ERROR"
                            myprocesstask.state = "0"
                            myprocesstask.content = "上传" + script_name + "脚本时，连接服务器失败。"
                            myprocesstask.steprun_id = steprun.id
                            myprocesstask.save()
                            return 0
                        else:
                            try:
                                sftp.put(local_file, linux_temp_script_file)
                            except FileNotFoundError as e:
                                scriptrun.runlog = "上传linux脚本文件失败。"  # 写入错误类型
                                scriptrun.explain = "上传linux脚本文件失败：{0}。".format(e)  # 写入错误类型
                                scriptrun.state = "ERROR"
                                scriptrun.save()
                                steprun.state = "ERROR"
                                steprun.save()

                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = steprun.processrun
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = steprun.processrun.creatuser
                                myprocesstask.receiveauth = steprun.step.group
                                myprocesstask.type = "ERROR"
                                myprocesstask.state = "0"
                                myprocesstask.content = "脚本" + script_name + "上传失败：{0}。".format(e)
                                myprocesstask.steprun_id = steprun.id
                                myprocesstask.save()
                                return 0
                            else:
                                sftp.chmod(linux_temp_script_file, int("755", 8))

                            ssh.close()
                        # 执行脚本(上传文件(dos格式>>shell))
                        exe_cmd = r"sed -i 's/\r$//' {0}&&sed -i 's/\r$//' {0}&&sh {0}".format(linux_temp_script_file)
                    else:
                        ############################
                        # 创建windows下目录:       #
                        #   先判断文件是否存在，再  #
                        #   mkdir/md path 创建文件 #
                        ############################
                        windows_temp_script_path = r"C:\drm\{processrunid}".format(**{"processrunid": processrun.id})
                        mkdir_cmd = "if not exist {windows_temp_script_path} mkdir {windows_temp_script_path}".format(
                            **{"windows_temp_script_path": windows_temp_script_path})
                        mkdir_obj = remote.ServerByPara(mkdir_cmd, ip, username, password, system_tag)
                        mkdir_result = mkdir_obj.run("")

                        windows_temp_script_name = "tmp_script_{scriptrun_id}.bat".format(**{"scriptrun_id": scriptrun.id})
                        windows_temp_script_file = windows_temp_script_path + r"\\" + windows_temp_script_name
                        script_text = content_load_params(script_instance)
                        para_list = script_text.split("\n")
                        for num, content in enumerate(para_list):
                            tmp_cmd = ""
                            if num == 0:
                                tmp_cmd = r"""echo {0}>{1}""".format(content, windows_temp_script_file)
                            else:
                                tmp_cmd = r"""echo {0}>>{1}""".format(content, windows_temp_script_file)

                            tmp_obj = remote.ServerByPara(tmp_cmd, ip, username, password, system_tag)
                            tmp_result = tmp_obj.run("")

                            if tmp_result["exec_tag"] == 1:
                                scriptrun.runlog = "上传windows脚本文件失败。"  # 写入错误类型
                                scriptrun.explain = "上传windows脚本文件失败：{0}。".format(tmp_result["data"])
                                scriptrun.state = "ERROR"
                                scriptrun.save()
                                steprun.state = "ERROR"
                                steprun.save()

                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = steprun.processrun
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = steprun.processrun.creatuser
                                myprocesstask.receiveauth = steprun.step.group
                                myprocesstask.type = "ERROR"
                                myprocesstask.state = "0"
                                myprocesstask.content = "脚本" + script_name + "上传windows脚本文件失败，请处理。"
                                myprocesstask.steprun_id = steprun.id
                                myprocesstask.save()
                                return 0

                        exe_cmd = windows_temp_script_file

                    # 执行文件
                    rm_obj = remote.ServerByPara(exe_cmd, ip, username, password, system_tag)
                    result = rm_obj.run(script.succeedtext)
                else:
                    result = {}
                    commvault_api_path = os.path.join(os.path.join(settings.BASE_DIR, "faconstor"),
                                                      "commvault_api") + os.sep + "{0}.py".format(script.commv_interface)

                    # 判断接口文件是否存在
                    interface_existed = os.path.exists(commvault_api_path)
                    if not interface_existed:
                        result["exec_tag"] = 1
                        result["data"] = "Commvault接口文件不存在。"
                        result["log"] = "Commvault接口文件不存在。"
                    else:
                        ret = ""

                        oracle_param = "{0} {1} {2} {3}".format(pri_id, std_id, instance_name, processrun.id)
                        try:
                            ret = subprocess.getstatusoutput(commvault_api_path + " {0}".format(oracle_param))
                            exec_status, recover_job_id = ret
                        except Exception as e:
                            result["exec_tag"] = 1
                            result["data"] = "执行commvault接口出现异常{0}。".format(e)
                            result["log"] = "执行commvault接口出现异常{0}。".format(e)
                        else:
                            if exec_status == 0:
                                result["exec_tag"] = 0
                                result["data"] = "调用commvault接口成功。"
                                result["log"] = "调用commvault接口成功。"
                            elif exec_status == 2:
                                #######################################
                                # ret=2时，查看任务错误信息写入日志       #
                                # Oracle恢复出错                      #
                                #######################################
                                recover_error = "无"
                                from .views import get_credit_info

                                try:
                                    _, sqlserver_credit = get_credit_info(utils_content)
                                    # 查看Oracle恢复错误信息
                                    dm = SQLApi.CVApi(sqlserver_credit)
                                    job_controller = dm.get_job_controller()
                                    dm.close()

                                    for jc in job_controller:
                                        if str(recover_job_id) == str(jc["jobID"]):
                                            recover_error = jc["delayReason"]
                                            break
                                except Exception as e:
                                    recover_error = e

                                result["exec_tag"] = 2
                                # 查看任务错误信息写入>>result["data"]
                                result["data"] = recover_error
                                result["log"] = "Oracle恢复出错。"
                            elif exec_status == 3:
                                result["exec_tag"] = 3
                                # 查看任务错误信息写入>>result["data"]
                                result["data"] = "长时间未获取到Commvault状态，请检查Commvault恢复情况。"
                                result["log"] = "长时间未获取到Commvault状态，请检查Commvault恢复情况。"
                            else:
                                result["exec_tag"] = 1
                                result["data"] = recover_job_id
                                result["log"] = recover_job_id

                scriptrun.result = result['exec_tag']
                scriptrun.explain = result['data']
                # 处理接口调用执行失败问题
                if result["exec_tag"] == 1:
                    scriptrun.runlog = result['log']  # 写入错误类型
                    scriptrun.explain = result['data']
                    scriptrun.state = "ERROR"
                    scriptrun.save()
                    steprun.state = "ERROR"
                    steprun.save()

                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = steprun.processrun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = steprun.processrun.creatuser
                    myprocesstask.receiveauth = steprun.step.group
                    myprocesstask.type = "ERROR"
                    myprocesstask.logtype = "SCRIPT"
                    myprocesstask.state = "0"
                    myprocesstask.content = "接口" + script_name + "调用执行失败，请处理。"
                    myprocesstask.steprun_id = steprun.id
                    myprocesstask.save()
                    return 0
                # Oracle恢复失败问题
                if result["exec_tag"] in [2, 3]:
                    scriptrun.runlog = result['log']  # 写入错误类型
                    scriptrun.explain = result['data']
                    scriptrun.state = "ERROR"
                    scriptrun.save()
                    steprun.state = "ERROR"
                    steprun.save()

                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = steprun.processrun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = steprun.processrun.creatuser
                    myprocesstask.receiveauth = steprun.step.group
                    myprocesstask.type = "ERROR"
                    myprocesstask.logtype = "SCRIPT"
                    myprocesstask.state = "0"
                    myprocesstask.steprun_id = steprun.id
                    if result["exec_tag"] == 2:
                        myprocesstask.content = "接口" + script_name + "调用过程中，Oracle恢复异常。"
                        myprocesstask.save()
                        # 辅助拷贝未完成
                        if "RMAN Script execution failed  with error [RMAN-03002" in result['data']:
                            # 终止commvault作业
                            if recover_job_id != '':
                                from .views import get_credit_info
                                try:
                                    commvault_credit, _ = get_credit_info(utils_content)
                                    cvToken = CV_RestApi_Token()
                                    cvToken.login(commvault_credit)
                                    cvOperate = CV_OperatorInterFace(cvToken)
                                    cvOperate.kill_job(recover_job_id)
                                except Exception as e:
                                    pass

                            myprocesstask.logtype = "STOP"
                            myprocesstask.content = "由于辅助拷贝未完成，本次演练中止。"
                            myprocesstask.save()
                            return 5
                    if result["exec_tag"] == 3:
                        myprocesstask.content = "接口" + script_name + "调用过程中，长时间未获取到Commvault状态，请检查Commvault恢复情况。"
                        myprocesstask.save()
                    return 0

                scriptrun.endtime = datetime.datetime.now()
                scriptrun.state = "DONE"
                scriptrun.save()

                myprocesstask = ProcessTask()
                myprocesstask.processrun = steprun.processrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = steprun.processrun.creatuser
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "SCRIPT"
                myprocesstask.state = "1"
                myprocesstask.content = "脚本" + script_name + "完成。"
                myprocesstask.save()

            if steprun.step.approval == "1" or steprun.verifyitemsrun_set.all():
                steprun.state = "CONFIRM"
                steprun.endtime = datetime.datetime.now()
                steprun.save()

                steprun_name = steprun.step.name if steprun.step.name else ""
                myprocesstask = ProcessTask()
                myprocesstask.processrun = steprun.processrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = steprun.processrun.creatuser
                myprocesstask.receiveauth = steprun.step.group
                myprocesstask.type = "RUN"
                myprocesstask.state = "0"
                task_content = "步骤" + steprun_name + "等待确认，请处理。"
                myprocesstask.content = task_content
                myprocesstask.steprun_id = steprun.id

                myprocesstask.save()

                return 2
            else:
                steprun.state = "DONE"
                steprun.endtime = datetime.datetime.now()
                steprun.save()

                steprun_name = steprun.step.name if steprun.step.name else ""
                myprocesstask = ProcessTask()
                myprocesstask.processrun = steprun.processrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = steprun.processrun.creatuser
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "STEP"
                myprocesstask.state = "1"
                myprocesstask.content = "步骤" + steprun_name + "完成。"
                myprocesstask.save()

        nextstep = steprun.step.next.exclude(state="9")
        if len(nextstep) > 0:
            # 演练中，后续步骤不计入RTO时，自动开启下一流程
            if processrun.walkthrough is not None and nextstep[
                0].rto_count_in == "0" and processrun.walkthroughstate != "DONE":
                processrun.walkthroughstate = "DONE"
                processrun.save()
                current_process_run = processrun.walkthrough.processrun_set.filter(state="PLAN")
                if current_process_run:
                    current_process_run = current_process_run[0]
                    current_process_run.starttime = datetime.datetime.now()
                    current_process_run.state = "RUN"
                    current_process_run.walkthroughstate = "RUN"
                    current_process_run.DataSet_id = 89
                    current_process_run.save()

                    process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").exclude(Q(type=None) | Q(type=""))

                    allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                        "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                    if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                        # 将当前流程改成SIGN
                        c_process_run_id = current_process_run.id
                        c_process_run = ProcessRun.objects.filter(id=c_process_run_id)
                        if c_process_run:
                            c_process_run = c_process_run[0]
                            c_process_run.state = "SIGN"
                            c_process_run.save()
                        for group in allgroup:
                            try:
                                signgroup = Group.objects.get(id=int(group["group"]))
                                groupname = signgroup.name
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = current_process_run
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = 'admin'
                                myprocesstask.receiveauth = group["group"]
                                myprocesstask.type = "SIGN"
                                myprocesstask.state = "0"
                                myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                                myprocesstask.save()
                            except:
                                pass

                    else:
                        prosssigns = ProcessTask.objects.filter(processrun=current_process_run, state="0")
                        if len(prosssigns) <= 0:
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = current_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.type = "INFO"
                            myprocesstask.logtype = "START"
                            myprocesstask.state = "1"
                            myprocesstask.senduser = 'admin'
                            myprocesstask.content = "流程启动。"
                            myprocesstask.save()

                            exec_process.delay(current_process_run.id)
                else:
                    walkthrough = processrun.walkthrough
                    walkthrough.state = "DONE"
                    walkthrough.endtime = datetime.datetime.now()
                    walkthrough.save()

            nextsteprun = nextstep[0].steprun_set.exclude(state="9").filter(processrun=steprun.processrun)
            if len(nextsteprun) > 0:
                # starttime存在，一级步骤不需要再次写入starttime
                nextsteprun = nextsteprun[0]
                start_time = nextsteprun.starttime

                if start_time:
                    if_repeat = True
                else:
                    if_repeat = False

                nextreturn = runstep(nextsteprun, if_repeat, processrun_params)

                if nextreturn == 0:
                    return 0
                if nextreturn == 2:
                    return 2

        return 1
    else:
        return 3


@shared_task
def exec_process(processrunid, if_repeat=False):
    """
    执行当前流程下的所有脚本
    """
    end_step_tag = 0
    processrun = ProcessRun.objects.filter(id=processrunid)
    processrun = processrun[0]
    
    # processrun_params 流程参数 传递
    processrun_params = {}
    
    # Commvault流程恢复 nextSCN选项
    # 流程恢复 ...ProcessRun>>copy_priority
    # 计划流程 ...Origin>>copy_priority
    #   先获取优先级 再获取nextSCN选项(主拷贝、辅助拷贝) 
    if processrun.process.type.upper() == "COMMVAULT":
        # 获取流程参数
        # utils.content copy_priority pri
        # 工具认证信息，恢复优先级，源客户端名称
        copy_priority = 1
        utils_content = ""
        pri_client_name = ""
        std_id = None
        pri = None
        info = processrun.info
        agent_type = ""
        instance_name = ""
        try:
            info = etree.XML(info)
        except Exception:
            pass
        else:
            pri_id = info.xpath("//param")[0].attrib.get("pri_id")
            try:
                pri = CvClient.objects.get(id=int(pri_id))
                pri_client_name = pri.client_name
                std_id = pri.destination_id
                utils_content = pri.utils.content if pri.utils else None
                agent_type = pri.agentType
                instance_name = pri.instanceName
            except Exception:
                pass
            processrun_params["pri_id"] = pri_id
            processrun_params["pri"] = pri
            processrun_params["std_id"] = std_id
            processrun_params["utils_content"] = utils_content
            
            if "Oracle" in agent_type:
                # 辅助拷贝暂时仅用在Oracle
                copy_priority = info.xpath("//param")[0].attrib.get("copy_priority")

                # nextSCN-1
                from .views import get_credit_info
                _, sqlserver_credit = get_credit_info(utils_content)

                dm = SQLApi.CVApi(sqlserver_credit)
                ret = dm.get_all_backup_job_list(pri_client_name, agent_type, instance_name)
                logger.info("%s %s %s" % (pri_client_name, agent_type, instance_name))
                logger.info(str(ret))
                
                # 无联机全备记录，请修改配置，完成联机全备后，待辅助拷贝结束后重启
                if not ret:
                    dm.close()
                    end_step_tag = 0
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = processrun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = processrun.creatuser
                    myprocesstask.receiveuser = processrun.creatuser
                    myprocesstask.type = "ERROR"
                    myprocesstask.state = "0"
                    myprocesstask.content = "无联机全备记录，请修改配置，完成联机全备后，待辅助拷贝结束后重启。"
                    myprocesstask.save()
                else:
                    curSCN = None

                    # ** 获得SCN号
                    # 指定时间 匹配该时间点的SCN
                    # 最新时间 匹配最新的SCN号
                    recover_time = '{:%Y-%m-%d %H:%M:%S}'.format(processrun.recover_time) if processrun.recover_time else ""
                    if recover_time:
                        for i in ret:
                            if i["subclient"] == "default" and i['LastTime'] == recover_time:
                                curSCN = i["cur_SCN"]
                                break
                    else:
                        # 当前时间点，选择最新的SCN号
                        for i in ret:
                            if i["subclient"] == "default":
                                curSCN = i["cur_SCN"]
                                break

                    # 辅助拷贝优先的恢复 最新
                    if copy_priority == 2:
                        if not recover_time:
                            tmp_tag = 0
                            for orcl_copy in ret:
                                if orcl_copy["idataagent"] == "Oracle Database":
                                    if dm.has_auxiliary_job(orcl_copy['jobId']):
                                        orcl_copy_starttime = datetime.datetime.strptime(orcl_copy['StartTime'], "%Y-%m-%d %H:%M:%S")
                                        curSCN = orcl_copy['cur_SCN']
                                        processrun.recover_time = orcl_copy_starttime if orcl_copy_starttime else None

                                        if tmp_tag > 0:
                                            break
                                        tmp_tag += 1
                                else:
                                    break

                    dm.close()

                    # 保存curSCN号至info
                    # 修改xml
                    info = processrun.info
                    try:
                        info = etree.XML(info)
                        node = info.xpath("//param")[0]
                        node.attrib["curSCN"] = str(curSCN)
                        content = etree.tounicode(node)
                    except Exception:
                        pass
                    else:
                        processrun.info = content
                        processrun.save()
 
    steprunlist = StepRun.objects.exclude(state="9").filter(processrun=processrun, step__last=None, step__pnode=None)
    if len(steprunlist) > 0:
        # 演练中，第一步不计入RTO时，自动开启下一流程
        if processrun.walkthrough is not None and steprunlist[0].step.rto_count_in == "0":
            processrun.walkthroughstate = "DONE"
            processrun.save()

            current_process_run = processrun.walkthrough.processrun_set.filter(state="PLAN")
            if current_process_run:
                current_process_run = current_process_run[0]
                current_process_run.starttime = datetime.datetime.now()
                current_process_run.state = "RUN"
                current_process_run.walkthroughstate = "RUN"
                
                process_type = current_process_run.process.type
                if process_type.upper() == "COMMVAULT":
                    cv_oracle_restore_params_save(current_process_run)
                
                current_process_run.save()

                process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").exclude(Q(type=None) | Q(type=""))

                allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                    "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                    # 将当前流程改成SIGN
                    c_process_run_id = current_process_run.id
                    c_process_run = ProcessRun.objects.filter(id=c_process_run_id)
                    if c_process_run:
                        c_process_run = c_process_run[0]
                        c_process_run.state = "SIGN"
                        c_process_run.save()
                    for group in allgroup:
                        try:
                            signgroup = Group.objects.get(id=int(group["group"]))
                            groupname = signgroup.name
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = current_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = 'admin'
                            myprocesstask.receiveauth = group["group"]
                            myprocesstask.type = "SIGN"
                            myprocesstask.state = "0"
                            myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                            myprocesstask.save()
                        except:
                            pass

                else:
                    prosssigns = ProcessTask.objects.filter(processrun=current_process_run, state="0")
                    if len(prosssigns) <= 0:
                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = current_process_run
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.type = "INFO"
                        myprocesstask.logtype = "START"
                        myprocesstask.state = "1"
                        myprocesstask.senduser = 'admin'
                        myprocesstask.content = "流程启动。"
                        myprocesstask.save()

                        exec_process.delay(current_process_run.id)
            else:
                walkthrough = processrun.walkthrough
                walkthrough.state = "DONE"
                walkthrough.endtime = datetime.datetime.now()
                walkthrough.save()

        end_step_tag = runstep(steprunlist[0], if_repeat, processrun_params)
    else:
        myprocesstask = ProcessTask()
        myprocesstask.processrun = processrun
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = processrun.creatuser
        myprocesstask.receiveuser = processrun.creatuser
        myprocesstask.type = "ERROR"
        myprocesstask.state = "0"
        myprocesstask.content = "流程配置错误，请处理。"
        myprocesstask.save()
    if end_step_tag == 0:
        processrun.state = "ERROR"
        processrun.save()
    if end_step_tag == 1:
        processrun = ProcessRun.objects.filter(id=processrunid)
        processrun = processrun[0]
        curwalkthroughstate = processrun.walkthroughstate
        processrun.state = "DONE"
        processrun.walkthroughstate = "DONE"
        processrun.endtime = datetime.datetime.now()
        processrun.save()
        myprocesstask = ProcessTask()
        myprocesstask.processrun = processrun
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = processrun.creatuser
        myprocesstask.type = "INFO"
        myprocesstask.logtype = "END"
        myprocesstask.state = "1"
        myprocesstask.content = "流程结束。"
        myprocesstask.save()

        # 演练中，当前力流程结束时，启动下一流程
        if processrun.walkthrough is not None:
            if curwalkthroughstate != "DONE":
                current_process_run = processrun.walkthrough.processrun_set.filter(state="PLAN")
                if current_process_run:
                    current_process_run = current_process_run[0]
                    current_process_run.starttime = datetime.datetime.now()
                    current_process_run.state = "RUN"
                    current_process_run.walkthroughstate = "RUN"
                    current_process_run.save()

                    process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").exclude(Q(type=None) | Q(type=""))

                    allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                        "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                    if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                        # 将当前流程改成SIGN
                        c_process_run_id = current_process_run.id
                        c_process_run = ProcessRun.objects.filter(id=c_process_run_id)
                        if c_process_run:
                            c_process_run = c_process_run[0]
                            c_process_run.state = "SIGN"
                            c_process_run.save()
                        for group in allgroup:
                            try:
                                signgroup = Group.objects.get(id=int(group["group"]))
                                groupname = signgroup.name
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = current_process_run
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = 'admin'
                                myprocesstask.receiveauth = group["group"]
                                myprocesstask.type = "SIGN"
                                myprocesstask.state = "0"
                                myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                                myprocesstask.save()
                            except:
                                pass

                    else:
                        prosssigns = ProcessTask.objects.filter(processrun=current_process_run, state="0")
                        if len(prosssigns) <= 0:
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = current_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.type = "INFO"
                            myprocesstask.logtype = "START"
                            myprocesstask.state = "1"
                            myprocesstask.senduser = 'admin'
                            myprocesstask.content = "流程启动。"
                            myprocesstask.save()

                            exec_process.delay(current_process_run.id)
                else:
                    walkthrough = processrun.walkthrough
                    walkthrough.state = "DONE"
                    walkthrough.endtime = datetime.datetime.now()
                    walkthrough.save()

    if end_step_tag == 5:
        processrun.state = "STOP"
        processrun.save()
        #
    #     processtasks = ProcessTask.objects.filter(state="0", processrun=processrun)
    #     if len(processtasks) > 0:
    #         processtasks[0].state = "1"
    #         processtasks[0].endtime = datetime.datetime.now()
    #         processtasks[0].save()
    # else:
    #     processrun.state = "ERROR"
    #     processrun.save()
    #     processtasks = ProcessTask.objects.filter(state="0", processrun=processrun)
    #     if len(processtasks) > 0:
    #         processtasks[0].state = "1"
    #         processtasks[0].save()
    #
    #         myprocesstask = ProcessTask()
    #         myprocesstask.processrun = processrun
    #         myprocesstask.starttime = datetime.datetime.now()
    #         myprocesstask.senduser = processtasks[0].senduser
    #         myprocesstask.receiveuser = processtasks[0].receiveuser
    #         myprocesstask.type = "RUN"
    #         myprocesstask.state = "0"
    #         myprocesstask.content = processrun.process.name + " 流程运行出错，请处理。"
    #         myprocesstask.save()


@shared_task
def create_process_run(*args, **kwargs):
    """
    创建计划流程
    :param process:
    :return:
    """
    # exec_process.delay(processrunid)
    # data_path/target/origin/
    try:
        process_id = int(kwargs["cur_process"])
    except ValueError as e:
        pass
    else:
        try:
            cur_process = Process.objects.get(id=process_id)
        except Process.DoesNotExist as e:
            print(e)
        else:
            running_process = ProcessRun.objects.filter(process=cur_process, state__in=["RUN"])
            if running_process.exists():
                myprocesstask = ProcessTask()
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "END"
                myprocesstask.state = "0"
                myprocesstask.processrun = running_process[0]
                myprocesstask.content = "计划流程({0})已运行，无法按计划创建恢复流程任务。".format(running_process[0].process.name)
                myprocesstask.save()
            else:
                myprocessrun = ProcessRun()
                myprocessrun.creatuser = kwargs["creatuser"]
                myprocessrun.process = cur_process
                myprocessrun.starttime = datetime.datetime.now()
                myprocessrun.state = "RUN"
                process_type = myprocessrun.process.type
                if process_type.upper() == "COMMVAULT":
                    cv_oracle_restore_params_save(myprocessrun)

                myprocessrun.save()
                mystep = cur_process.step_set.exclude(state="9")
                if not mystep.exists():
                    myprocesstask = ProcessTask()
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.type = "INFO"
                    myprocesstask.logtype = "END"
                    myprocesstask.state = "0"
                    myprocesstask.processrun = myprocessrun
                    myprocesstask.content = "计划流程({0})不存在可运行步骤，无法按计划创建恢复流程任务。".format(myprocessrun.process.name)
                    myprocesstask.save()
                else:
                    for step in mystep:
                        mysteprun = StepRun()
                        mysteprun.step = step
                        mysteprun.processrun = myprocessrun
                        mysteprun.state = "EDIT"
                        mysteprun.save()

                        myscript = step.script_set.exclude(state="9")
                        for script in myscript:
                            myscriptrun = ScriptRun()
                            myscriptrun.script = script
                            myscriptrun.steprun = mysteprun
                            myscriptrun.state = "EDIT"
                            myscriptrun.save()

                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = myprocessrun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.type = "INFO"
                    myprocesstask.logtype = "START"
                    myprocesstask.state = "1"
                    myprocesstask.content = "流程已启动。"
                    myprocesstask.save()

                    exec_process.delay(myprocessrun.id)


def cv_restore_params_save(processrun):
    """
    保存 Commvault Oracle 恢复需要的参数
    Args:
        processrun 流程对象
    """
    # 计划流程用的是默认 恢复选项
    # 计划流程如果是Commvault 在流程中首个 客户端 对应的 恢复选项 写到ProcessRun
    try:
        pri_id, std_id, cv_client_info = "", "", ""
        process = processrun.process

        # 过滤所有脚本
        all_steps = process.step_set.exclude(state="9")
        for cur_step in all_steps:
            script_instances = cur_step.scriptinstance_set.exclude(state="9")
            for script_instance in script_instances:
                if script_instance.primary:
                    pri = script_instance.primary
                    pri_id = pri.id
                    std_id = pri.destination.id if pri.destination else ""
                    cv_client_info = pri.info
                    break
        try:
            cv_client_info = etree.XML(cv_client_info)
            node = cv_client_info.xpath("//param")[0]
            node.attrib["pri_id"] = str(pri_id)
            node.attrib["std_id"] = str(std_id)
            content = etree.tounicode(node)
            processrun.info = content
            processrun.save()
        except Exception as e:
            logger.info(str(e))
    except Exception as e:
        logger.info(str(e))