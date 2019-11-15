from __future__ import absolute_import
from celery import shared_task
from faconstor.models import *
from django.db import connection
from xml.dom.minidom import parse, parseString
from . import remote
from .models import *
import datetime
from django.db.models import Q
import time
import paramiko
import os
from TSDRM import settings


def is_connection_usable():
    try:
        connection.connection.ping()
    except:
        return False
    else:
        return True





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
    for script in scriptruns:
        script.starttime = datetime.datetime.now()
        script.result = ""
        script.state = "RUN"
        script.save()
        # 执行脚本内容
        # cmd = r"{0}".format(script.script.scriptpath + script.script.filename)
        cmd = r"{0}".format(script.script.script_text)

        # HostsManage
        cur_host_manage = script.script.hosts_manage
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
        result = rm_obj.run(script.script.succeedtext)

        script.endtime = datetime.datetime.now()
        script.result = result["exec_tag"]
        script.explain = result['data']

        # 处理脚本执行失败问题
        if result["exec_tag"] == 1:
            script.runlog = result['log']
            script.explain = result['data']

            end_step_tag = False
            script.state = "ERROR"
            steprun.state = "ERROR"
            script.save()
            steprun.save()
            break
        script.state = "DONE"
        script.save()

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
                for script in cur_step_scripts:
                    script.starttime = datetime.datetime.now()
                    script.result = ""
                    script.state = "RUN"
                    script.save()

                    # HostsManage
                    cur_host_manage = script.script.hosts_manage
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

                        linux_temp_script_name = "tmp_script_{scriptrun_id}.sh".format(**{"scriptrun_id": script.id})
                        linux_temp_script_file = linux_temp_script_path + "/" + linux_temp_script_name

                        # 写入本地文件
                        script_path = os.path.join(os.path.join(os.path.join(settings.BASE_DIR, "faconstor"), "upload"),
                                                   "script")

                        local_file = script_path + os.sep + "{0}_local_script.sh".format(processrun.process.name)

                        try:
                            with open(local_file, "w") as f:
                                f.write(script.script.script_text)
                        except FileNotFoundError as e:
                            script.runlog = "Linux脚本写入本地失败。"  # 写入错误类型
                            script.explain = "Linux脚本写入本地失败：{0}。".format(e)
                            script.state = "ERROR"
                            script.save()
                            steprun.state = "ERROR"
                            steprun.save()

                            # script_name = script.script.name if script.script.name else ""
                            # myprocesstask = ProcessTask()
                            # myprocesstask.processrun = steprun.processrun
                            # myprocesstask.starttime = datetime.datetime.now()
                            # myprocesstask.senduser = steprun.processrun.creatuser
                            # myprocesstask.receiveauth = steprun.step.group
                            # myprocesstask.type = "ERROR"
                            # myprocesstask.state = "0"
                            # myprocesstask.content = "Linux脚本" + script_name + "内容写入失败，请处理。"
                            # myprocesstask.steprun_id = steprun.id
                            # myprocesstask.save()
                        else:
                            # 上传Linux服务器
                            try:
                                ssh = paramiko.Transport((ip, 22))
                                ssh.connect(username=username, password=password)
                                sftp = paramiko.SFTPClient.from_transport(ssh)
                            except paramiko.ssh_exception.SSHException as e:
                                script.runlog = "连接服务器失败。"  # 写入错误类型
                                script.explain = "连接服务器失败：{0}。".format(e)  # 写入错误类型
                                script.state = "ERROR"
                                script.save()
                                steprun.state = "ERROR"
                                steprun.save()

                                # script_name = script.script.name if script.script.name else ""
                                # myprocesstask = ProcessTask()
                                # myprocesstask.processrun = steprun.processrun
                                # myprocesstask.starttime = datetime.datetime.now()
                                # myprocesstask.senduser = steprun.processrun.creatuser
                                # myprocesstask.receiveauth = steprun.step.group
                                # myprocesstask.type = "ERROR"
                                # myprocesstask.state = "0"
                                # myprocesstask.content = "上传" + script_name + "脚本时，连接服务器失败。"
                                # myprocesstask.steprun_id = steprun.id
                                # myprocesstask.save()
                            else:
                                try:
                                    sftp.put(local_file, linux_temp_script_file)
                                except FileNotFoundError as e:
                                    script.runlog = "上传linux脚本文件失败。"  # 写入错误类型
                                    script.explain = "上传linux脚本文件失败：{0}。".format(e)  # 写入错误类型
                                    script.state = "ERROR"
                                    script.save()
                                    steprun.state = "ERROR"
                                    steprun.save()
                                    #
                                    # script_name = script.script.name if script.script.name else ""
                                    # myprocesstask = ProcessTask()
                                    # myprocesstask.processrun = steprun.processrun
                                    # myprocesstask.starttime = datetime.datetime.now()
                                    # myprocesstask.senduser = steprun.processrun.creatuser
                                    # myprocesstask.receiveauth = steprun.step.group
                                    # myprocesstask.type = "ERROR"
                                    # myprocesstask.state = "0"
                                    # myprocesstask.content = "脚本" + script_name + "上传失败：{0}。".format(e)
                                    # myprocesstask.steprun_id = steprun.id
                                    # myprocesstask.save()
                                else:
                                    sftp.chmod(linux_temp_script_file, 755)

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

                        windows_temp_script_name = "tmp_script_{scriptrun_id}.bat".format(**{"scriptrun_id": script.id})
                        windows_temp_script_file = windows_temp_script_path + r"\\" + windows_temp_script_name
                        para_list = script.script.script_text.split("\n")
                        for num, content in enumerate(para_list):
                            tmp_cmd = ""
                            if num == 0:
                                tmp_cmd = r"""echo {0}>{1}""".format(content, windows_temp_script_file)
                            else:
                                tmp_cmd = r"""echo {0}>>{1}""".format(content, windows_temp_script_file)

                            tmp_obj = remote.ServerByPara(tmp_cmd, ip, username, password, system_tag)
                            tmp_result = tmp_obj.run("")

                            if tmp_result["exec_tag"] == 1:
                                script.runlog = "上传windows脚本文件失败。"  # 写入错误类型
                                script.explain = "上传windows脚本文件失败：{0}。".format(tmp_result["data"])
                                script.state = "ERROR"
                                script.save()
                                steprun.state = "ERROR"
                                steprun.save()
                                #
                                # script_name = script.script.name if script.script.name else ""
                                # myprocesstask = ProcessTask()
                                # myprocesstask.processrun = steprun.processrun
                                # myprocesstask.starttime = datetime.datetime.now()
                                # myprocesstask.senduser = steprun.processrun.creatuser
                                # myprocesstask.receiveauth = steprun.step.group
                                # myprocesstask.type = "ERROR"
                                # myprocesstask.state = "0"
                                # myprocesstask.content = "脚本" + script_name + "上传windows脚本文件失败，请处理。"
                                # myprocesstask.steprun_id = steprun.id
                                # myprocesstask.save()

                        exe_cmd = windows_temp_script_file

                    # 执行文件
                    rm_obj = remote.ServerByPara(exe_cmd, ip, username, password, system_tag)
                    result = rm_obj.run(script.script.succeedtext)

                    script.endtime = datetime.datetime.now()
                    script.result = result['exec_tag']
                    script.explain = result['data']

                    # 处理脚本执行失败问题
                    if result["exec_tag"] == 1:
                        script.runlog = result['log']  # 写入错误类型
                        script.explain = result['data']
                        print("当前脚本执行失败,结束任务!")
                        script.state = "ERROR"
                        script.save()
                        steprun.state = "ERROR"
                        steprun.save()

                        # script_name = script.script.name if script.script.name else ""
                        # myprocesstask = ProcessTask()
                        # myprocesstask.processrun = steprun.processrun
                        # myprocesstask.starttime = datetime.datetime.now()
                        # myprocesstask.senduser = steprun.processrun.creatuser
                        # myprocesstask.receiveauth = steprun.step.group
                        # myprocesstask.type = "ERROR"
                        # myprocesstask.state = "0"
                        # myprocesstask.content = "脚本" + script_name + "执行错误，请处理。"
                        # myprocesstask.steprun_id = steprun.id
                        # myprocesstask.save()
                    else:
                        script.endtime = datetime.datetime.now()
                        script.state = "DONE"
                        script.save()

                        script_name = script.script.name if script.script.name else ""

                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = steprun.processrun
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = steprun.processrun.creatuser
                        myprocesstask.type = "INFO"
                        myprocesstask.logtype = "SCRIPT"
                        myprocesstask.state = "1"
                        myprocesstask.content = "脚本" + script_name + "完成。"
                        myprocesstask.save()


def runstep(steprun, if_repeat=False):
    """
    执行当前步骤下的所有脚本
    返回值0,：错误，1：完成，2：确认，3：流程已结束
    if_repeat用于避免已执行步骤重复执行。
    """
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
                        childreturn = runstep(childsteprun, if_repeat)
                        if childreturn == 0:
                            return 0
                        if childreturn == 2:
                            return 2
            scriptruns = steprun.scriptrun_set.exclude(Q(state__in=("9", "DONE", "IGNORE")) | Q(result=0))
            for script in scriptruns:
                # 目的：不在服务器存放脚本；
                #   Linux：通过ssh上传文件至服务器端；执行脚本；删除脚本；
                #   Windows：通过>/>> 逐行重定向字符串至服务端文件；执行脚本；删除脚本；

                script.starttime = datetime.datetime.now()
                script.result = ""
                script.state = "RUN"
                script.save()

                # HostsManage
                cur_host_manage = script.script.hosts_manage
                ip = cur_host_manage.host_ip
                username = cur_host_manage.username
                password = cur_host_manage.password
                script_type = cur_host_manage.type

                system_tag = ""
                if script_type == "SSH":
                    system_tag = "Linux"
                if script_type == "BAT":
                    system_tag = "Windows"

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

                    linux_temp_script_name = "tmp_script_{scriptrun_id}.sh".format(**{"scriptrun_id": script.id})
                    linux_temp_script_file = linux_temp_script_path + "/" + linux_temp_script_name

                    # 写入本地文件
                    script_path = os.path.join(os.path.join(os.path.join(settings.BASE_DIR, "faconstor"), "upload"),
                                               "script")

                    local_file = script_path + os.sep + "{0}_local_script.sh".format(processrun.process.name)

                    try:
                        with open(local_file, "w") as f:
                            f.write(script.script.script_text)
                    except FileNotFoundError as e:
                        script.runlog = "Linux脚本写入本地失败。"  # 写入错误类型
                        script.explain = "Linux脚本写入本地失败：{0}。".format(e)
                        script.state = "ERROR"
                        script.save()
                        steprun.state = "ERROR"
                        steprun.save()

                        script_name = script.script.name if script.script.name else ""
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
                        script.runlog = "连接服务器失败。"  # 写入错误类型
                        script.explain = "连接服务器失败：{0}。".format(e)  # 写入错误类型
                        script.state = "ERROR"
                        script.save()
                        steprun.state = "ERROR"
                        steprun.save()

                        script_name = script.script.name if script.script.name else ""
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
                            script.runlog = "上传linux脚本文件失败。"  # 写入错误类型
                            script.explain = "上传linux脚本文件失败：{0}。".format(e)  # 写入错误类型
                            script.state = "ERROR"
                            script.save()
                            steprun.state = "ERROR"
                            steprun.save()

                            script_name = script.script.name if script.script.name else ""
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
                            sftp.chmod(linux_temp_script_file, 755)

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

                    windows_temp_script_name = "tmp_script_{scriptrun_id}.bat".format(**{"scriptrun_id": script.id})
                    windows_temp_script_file = windows_temp_script_path + r"\\" + windows_temp_script_name
                    para_list = script.script.script_text.split("\n")
                    for num, content in enumerate(para_list):
                        tmp_cmd = ""
                        if num == 0:
                            tmp_cmd = r"""echo {0}>{1}""".format(content, windows_temp_script_file)
                        else:
                            tmp_cmd = r"""echo {0}>>{1}""".format(content, windows_temp_script_file)

                        tmp_obj = remote.ServerByPara(tmp_cmd, ip, username, password, system_tag)
                        tmp_result = tmp_obj.run("")

                        if tmp_result["exec_tag"] == 1:
                            script.runlog = "上传windows脚本文件失败。"  # 写入错误类型
                            script.explain = "上传windows脚本文件失败：{0}。".format(tmp_result["data"])
                            script.state = "ERROR"
                            script.save()
                            steprun.state = "ERROR"
                            steprun.save()

                            script_name = script.script.name if script.script.name else ""
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
                result = rm_obj.run(script.script.succeedtext)

                script.endtime = datetime.datetime.now()
                script.result = result['exec_tag']
                script.explain = result['data']

                # 处理脚本执行失败问题
                if result["exec_tag"] == 1:
                    script.runlog = result['log']  # 写入错误类型
                    script.explain = result['data']
                    print("当前脚本执行失败,结束任务!")
                    script.state = "ERROR"
                    script.save()
                    steprun.state = "ERROR"
                    steprun.save()

                    script_name = script.script.name if script.script.name else ""
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = steprun.processrun
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = steprun.processrun.creatuser
                    myprocesstask.receiveauth = steprun.step.group
                    myprocesstask.type = "ERROR"
                    myprocesstask.state = "0"
                    myprocesstask.content = "脚本" + script_name + "执行错误，请处理。"
                    myprocesstask.steprun_id = steprun.id
                    myprocesstask.save()
                    return 0

                script.endtime = datetime.datetime.now()
                script.state = "DONE"
                script.save()

                script_name = script.script.name if script.script.name else ""

                myprocesstask = ProcessTask()
                myprocesstask.processrun = steprun.processrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = steprun.processrun.creatuser
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "SCRIPT"
                myprocesstask.state = "1"
                myprocesstask.content = "脚本" + script_name + "完成。"
                myprocesstask.save()

                # 删除Linux下脚本
                # if system_tag == "Linux":
                #     del_cmd = 'if [ ! -f "{0}" ]; then'.format(linux_temp_script_file) + '\n' + \
                #               '   echo "文件不存在"' + '\n' + \
                #               'else' + '\n' + \
                #               '   rm -f {0}'.format(linux_temp_script_file) + '\n' + \
                #               'fi'
                #     del_obj = remote.ServerByPara(del_cmd, ip, username, password, system_tag)
                #     del_result = del_obj.run("")
                # else:
                #     if result["exec_tag"] == 0:
                #         # 删除windows的bat脚本
                #         del_cmd = 'if exist {0} del "{0}"'.format(windows_temp_script_file)
                #         del_obj = remote.ServerByPara(del_cmd, ip, username, password, system_tag)
                #         del_result = del_obj.run("")

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
            if processrun.walkthrough is not None and nextstep[0].rto_count_in == "0" and processrun.walkthroughstate != "DONE":
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

                    process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").filter(
                        type="falconstor")

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

                nextreturn = runstep(nextsteprun, if_repeat)

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
                current_process_run.save()

                process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").filter(
                    type="falconstor")

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

        end_step_tag = runstep(steprunlist[0], if_repeat)
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

                    process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").filter(
                        type="falconstor")

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
