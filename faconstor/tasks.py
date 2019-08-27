from __future__ import absolute_import
from celery import shared_task
import pymssql
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


def handle_func(jobid, steprunid):
    if not is_connection_usable():
        connection.close()
    try:
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()
    except:
        print("链接失败!")
    else:
        try:
            cur.execute(
                """SELECT *  FROM [commserv].[dbo].[RunningBackups] where jobid={0}""".format(jobid))
            backup_task_list = cur.fetchall()

            cur.execute(
                """SELECT *  FROM [commserv].[dbo].[RunningRestores] where jobid={0}""".format(jobid))
            restore_task_list = cur.fetchall()
        except:
            print("任务不存在!")  # 1.修改当前步骤状态为DONE
        else:
            # 查询备份/恢复是否报错，将报错信息写入当前Step的operator字段中，并结束当前任务
            if backup_task_list:
                for backup_job in backup_task_list:
                    print("备份进度：", backup_job[42])
                    if backup_job[42] == 100:
                        steprun = StepRun.objects.filter(id=steprunid)
                        steprun = steprun[0]
                        if backup_job["DelayReason"]:
                            steprun.operator = backup_job["DelayReason"]
                            steprun.state = "EDIT"
                            steprun.save()
                            cur.close()
                            conn.close()
                            return
                        else:
                            steprun.state = "DONE"
                            steprun.save()
                            cur.close()
                            conn.close()
                    else:
                        cur.close()
                        conn.close()
                        time.sleep(30)
                        handle_func(jobid, steprunid)
            elif restore_task_list:
                for restore_job in restore_task_list:
                    print("恢复进度：", restore_job[35])
                    if restore_job[35] == 100:
                        steprun = StepRun.objects.filter(id=steprunid)
                        steprun = steprun[0]
                        if restore_job["DelayReason"]:
                            steprun.operator = restore_job["DelayReason"]
                            steprun.save()
                            cur.close()
                            conn.close()
                            return
                        else:
                            steprun.state = "DONE"
                            steprun.save()
                            cur.close()
                            conn.close()
                    else:
                        cur.close()
                        conn.close()
                        time.sleep(30)
                        handle_func(jobid, steprunid)
            else:
                print("当前没有在执行的任务!")
                steprun = StepRun.objects.filter(id=steprunid)
                steprun = steprun[0]
                steprun.state = "DONE"
                steprun.save()


@shared_task
def handle_job(jobid, steprunid):
    """
    根据jobid查询任务状态，每半分钟查询一次，如果完成就在steprun中写入DONE
    """
    handle_func(jobid, steprunid)


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
        script.explain = result['data'] if len(result['data']) <= 5000 else result['data'][-4999:]

        # 处理脚本执行失败问题
        if result["exec_tag"] == 1:
            script.runlog = result['log']

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

                linux_temp_script_file = "/tmp/tmp_script.sh"
                # windows_temp_script_file = "C:/tmp_script{0}.bat".format(script.id)
                windows_temp_script_file = "C:/tmp_script.bat"
                if system_tag == "Linux":
                    # 写入文件
                    script_path = os.path.join(os.path.join(os.path.join(settings.BASE_DIR, "faconstor"), "upload"),
                                               "script")

                    local_file = script_path + os.sep + "{0}_local_script.sh".format(processrun.process.name)

                    with open(local_file, "w") as f:
                        f.write(script.script.script_text)

                    # 上传Linux服务器
                    ssh = paramiko.Transport((ip, 22))
                    ssh.connect(username=username, password=password)
                    sftp = paramiko.SFTPClient.from_transport(ssh)

                    remote_file = "/tmp/tmp_script.sh"
                    try:
                        sftp.put(local_file, remote_file)
                    except Exception as e:
                        script.runlog = "上传linux脚本文件失败。"  # 写入错误类型
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
                        myprocesstask.content = "脚本" + script_name + "内容写入失败，请处理。"
                        myprocesstask.steprun_id = steprun.id
                        myprocesstask.save()
                        return 0
                    ssh.close()

                    # 添加可执行权限
                    wt_cmd = r"""chmod 755 {0}""".format(linux_temp_script_file)
                    # 写死路径/tmp
                    script_wt = remote.ServerByPara(wt_cmd, ip, username, password, system_tag)
                    script_wt_result = script_wt.run("")

                    # 执行脚本
                    exe_cmd = r"sed -i 's/\r$//' {0}&&{0}".format(linux_temp_script_file)
                else:
                    # 上传文件(dos格式>>shell)
                    wt_cmd = r"""echo {0}>{1}&&if exist {1} echo 'file_existed'""".format(script.script.script_text, windows_temp_script_file)
                    wt_obj = remote.ServerByPara(wt_cmd, ip, username, password, system_tag)
                    wt_result = wt_obj.run("file_existed")

                    if wt_result["exec_tag"] == 1:
                        script.runlog = "上传windows脚本文件失败。"  # 写入错误类型
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
                        myprocesstask.content = "脚本" + script_name + "内容写入失败，请处理。"
                        myprocesstask.steprun_id = steprun.id
                        myprocesstask.save()
                        return 0

                    exe_cmd = windows_temp_script_file

                # 执行文件
                rm_obj = remote.ServerByPara(exe_cmd, ip, username, password, system_tag)
                result = rm_obj.run(script.script.succeedtext)

                script.endtime = datetime.datetime.now()
                script.result = result['exec_tag']
                script.explain = result['data'] if len(result['data']) <= 5000 else result['data'][-4999:]

                # 处理脚本执行失败问题
                if result["exec_tag"] == 1:
                    script.runlog = result['log']  # 写入错误类型
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
                if system_tag == "Linux":
                    del_cmd = 'if [ ! -f "{0}" ]; then'.format(linux_temp_script_file) + '\n' + \
                              '   echo "文件不存在"' + '\n' + \
                              'else' + '\n' + \
                              '   rm -f {0}'.format(linux_temp_script_file) + '\n' + \
                              'fi'
                    del_obj = remote.ServerByPara(del_cmd, ip, username, password, system_tag)
                    del_result = del_obj.run("")
                else:
                    if result["exec_tag"] == 0:
                        # 删除windows的bat脚本
                        del_cmd = 'if exist {0} del "{0}"'.format(windows_temp_script_file)
                        del_obj = remote.ServerByPara(del_cmd, ip, username, password, system_tag)
                        del_result = del_obj.run("")

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
        processrun.state = "DONE"
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
