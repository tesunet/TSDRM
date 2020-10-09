# 历史查询:演练查询、任务查询、知识库、通讯录
from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse

from django.contrib.auth.decorators import login_required
from faconstor.models import *
import json
from .views import getpagefuns
from django.template.response import TemplateResponse
import datetime
import os
from django.http import StreamingHttpResponse
import sys
import pdfkit
from django.db import connection
from django.db.models import Q
from TSDRM import settings


def file_iterator(file_name, chunk_size=512):
    with open(file_name, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


@login_required
def custom_pdf_report(request):
    """
    pip3 install pdfkit
    wkhtmltopdf安装文件已经在项目中static/process
    """
    processrun_id = request.GET.get("processrunid", "")
    process_id = request.GET.get("processid", "")

    # 构造数据
    # 1.获取当前流程对象
    process_run_objs = ProcessRun.objects.filter(id=processrun_id)
    if process_run_objs:
        process_run_obj = process_run_objs[0]
    else:
        raise Http404()

    # 2.报表封页文字
    title_xml = "自动化切换流程"
    abstract_xml = "切换报告"

    # 3.章节名称
    ele_xml01 = "一、切换概述"
    ele_xml02 = "二、步骤详情"

    # 4.构造第一章数据: first_el_dict
    # 切换概述节点下内容,有序字典中存放
    first_el_dict = {}

    start_time = process_run_obj.starttime
    end_time = process_run_obj.endtime
    create_user = process_run_obj.creatuser
    users = User.objects.filter(username=create_user)
    if users:
        create_user = users[0].userinfo.fullname
    else:
        create_user = ""
    run_reason = process_run_obj.run_reason

    first_el_dict["start_time"] = r"{0}".format(
        start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "")
    first_el_dict["end_time"] = r"{0}".format(
        end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "")

    all_step_runs = process_run_obj.steprun_set.exclude(state="9").exclude(step__rto_count_in="0").filter(
        step__pnode=None)
    step_rto = 0
    if all_step_runs:
        for step_run in all_step_runs:
            rto = 0
            end_time = step_run.endtime
            start_time = step_run.starttime
            if end_time and start_time:
                delta_time = (end_time - start_time)
                rto = delta_time.total_seconds()
            step_rto += rto

    # 扣除子级步骤中可能的rto_count_in的时间
    all_inner_step_runs = process_run_obj.steprun_set.exclude(state="9").filter(
        step__rto_count_in="0").exclude(
        step__pnode=None)
    inner_rto_not_count_in = 0
    if all_inner_step_runs:
        for inner_step_run in all_inner_step_runs:
            end_time = inner_step_run.endtime
            start_time = inner_step_run.starttime
            if end_time and start_time:
                delta_time = (end_time - start_time)
                rto = delta_time.total_seconds()
                inner_rto_not_count_in += rto
                step_rto -= inner_rto_not_count_in

    m, s = divmod(step_rto, 60)
    h, m = divmod(m, 60)
    first_el_dict["rto"] = "%d时%02d分%02d秒" % (h, m, s)

    first_el_dict["create_user"] = r"{0}".format(create_user)

    task_sign_obj = ProcessTask.objects.filter(processrun_id=processrun_id).exclude(state="9").filter(
        type="SIGN")

    if task_sign_obj:
        receiveusers = ""
        for task in task_sign_obj:
            receiveuser = task.receiveuser

            users = User.objects.filter(username=receiveuser)
            if users:
                receiveuser = users[0].userinfo.fullname

            if receiveuser:
                receiveusers += receiveuser + "、"

        first_el_dict["receiveuser"] = r"{0}".format(receiveusers[:-1])

    all_steprun_objs = StepRun.objects.filter(processrun_id=processrun_id)
    operators = ""
    for steprun_obj in all_steprun_objs:
        if steprun_obj.operator:
            if steprun_obj.operator not in operators:
                users = User.objects.filter(username=steprun_obj.operator)
                if users:
                    operator = users[0].userinfo.fullname
                    if operator:
                        if operator not in operators:
                            operators += operator + "、"

    first_el_dict["operator"] = r"{0}".format(operators[:-1])
    first_el_dict["run_reason"] = r"{0}".format(run_reason)

    # 构造第二章数据: step_info_list
    step_info_list = []
    pnode_steplist = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
        pnode_id=None)
    for num, pstep in enumerate(pnode_steplist):
        second_el_dict = dict()
        step_name = "{0}.{1}".format(num + 1, pstep.name)
        second_el_dict["step_name"] = step_name

        pnode_steprun = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id).filter(
            step=pstep)
        if pnode_steprun:
            pnode_steprun = pnode_steprun[0]
            if pnode_steprun.step.rto_count_in == "0":
                second_el_dict["start_time"] = ""
                second_el_dict["end_time"] = ""
                second_el_dict["rto"] = ""
            else:
                second_el_dict["start_time"] = pnode_steprun.starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                    pnode_steprun.starttime else ""
                second_el_dict["end_time"] = pnode_steprun.endtime.strftime(
                    "%Y-%m-%d %H:%M:%S") if pnode_steprun.endtime else ""

                if pnode_steprun.endtime and pnode_steprun.starttime:
                    end_time = pnode_steprun.endtime.strftime("%Y-%m-%d %H:%M:%S")
                    start_time = pnode_steprun.starttime.strftime("%Y-%m-%d %H:%M:%S")
                    delta_seconds = datetime.datetime.strptime(end_time,
                                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                        start_time, '%Y-%m-%d %H:%M:%S')
                    hour, minute, second = str(delta_seconds).split(":")

                    delta_time = "{0}时{1}分{2}秒".format(hour, minute, second)

                    second_el_dict["rto"] = delta_time
                else:
                    second_el_dict["rto"] = ""

        # 步骤负责人
        try:
            users = User.objects.filter(username=pnode_steprun.operator)
        except:
            if users:
                operator = users[0].userinfo.fullname
                second_el_dict["operator"] = operator
            else:
                second_el_dict["operator"] = ""

        # 当前步骤下脚本
        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "": "",
        }

        current_scripts = ScriptInstance.objects.exclude(state="9").filter(step_id=pstep.id).order_by("sort")
        script_list_wrapper = []
        if current_scripts:
            for snum, current_script in enumerate(current_scripts):
                script_el_dict = dict()
                # title
                script_name = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                script_el_dict["script_name"] = script_name
                # content
                steprun_id = pnode_steprun.id if pnode_steprun else None
                script_id = current_script.id
                current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id, script_id=script_id)
                if current_scriptrun_obj:
                    current_scriptrun_obj = current_scriptrun_obj[0]
                    script_el_dict["start_time"] = current_scriptrun_obj.starttime.strftime(
                        "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.starttime else ""
                    script_el_dict["end_time"] = current_scriptrun_obj.endtime.strftime(
                        "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.endtime else ""

                    if current_scriptrun_obj.endtime and current_scriptrun_obj.starttime:
                        end_time = current_scriptrun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S")
                        start_time = current_scriptrun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S")
                        delta_seconds = datetime.datetime.strptime(end_time,
                                                                   '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                            start_time, '%Y-%m-%d %H:%M:%S')
                        hour, minute, second = str(delta_seconds).split(":")

                        delta_time = "{0}时{1}分{2}秒".format(hour, minute, second)

                        script_el_dict["rto"] = delta_time
                    else:
                        script_el_dict["rto"] = ""

                    state = current_scriptrun_obj.state
                    if state in state_dict.keys():
                        script_el_dict["state"] = state_dict[state]
                    else:
                        script_el_dict["state"] = ""
                    script_el_dict["explain"] = current_scriptrun_obj.explain

                script_list_wrapper.append(script_el_dict)
            second_el_dict["script_list_wrapper"] = script_list_wrapper

        # 子步骤下相关内容
        p_id = pstep.id
        inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
            pnode_id=p_id)

        inner_step_list = []
        if inner_steps:
            for num, step in enumerate(inner_steps):
                inner_second_el_dict = dict()
                step_name = "{0}){1}".format(num + 1, step.name)
                inner_second_el_dict["step_name"] = step_name
                steprun_obj = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id).filter(
                    step=step)
                if steprun_obj:
                    steprun_obj = steprun_obj[0]
                    if steprun_obj.step.rto_count_in == "0":
                        inner_second_el_dict["start_time"] = ""
                        inner_second_el_dict["end_time"] = ""
                        inner_second_el_dict["rto"] = ""
                    else:
                        inner_second_el_dict["start_time"] = steprun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                            steprun_obj.starttime else ""
                        inner_second_el_dict["end_time"] = steprun_obj.endtime.strftime(
                            "%Y-%m-%d %H:%M:%S") if steprun_obj.endtime else ""

                        if steprun_obj.endtime and steprun_obj.starttime:
                            end_time = steprun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S")
                            start_time = steprun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S")
                            delta_seconds = datetime.datetime.strptime(end_time,
                                                                       '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                start_time, '%Y-%m-%d %H:%M:%S')
                            hour, minute, second = str(delta_seconds).split(":")

                            delta_time = "{0}时{1}分{2}秒".format(hour, minute, second)

                            inner_second_el_dict["rto"] = delta_time
                        else:
                            inner_second_el_dict["rto"] = ""

                    # 步骤负责人
                    users = User.objects.filter(username=steprun_obj.operator)
                    if users:
                        operator = users[0].userinfo.fullname
                        inner_second_el_dict["operator"] = operator
                    else:
                        inner_second_el_dict["operator"] = ""

                    # 当前步骤下脚本
                    current_scripts = ScriptInstance.objects.exclude(state="9").filter(step_id=step.id).order_by("sort")

                    script_list_inner = []
                    if current_scripts:
                        for snum, current_script in enumerate(current_scripts):
                            script_el_dict_inner = dict()
                            # title
                            script_name = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                            script_el_dict_inner["script_name"] = script_name

                            # content
                            steprun_id = steprun_obj.id
                            script_id = current_script.id
                            current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id,
                                                                             script_id=script_id)
                            if current_scriptrun_obj:
                                current_scriptrun_obj = current_scriptrun_obj[0]
                                script_el_dict_inner["start_time"] = current_scriptrun_obj.starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.starttime else ""
                                script_el_dict_inner["end_time"] = current_scriptrun_obj.endtime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.endtime else ""

                                if current_scriptrun_obj.endtime and current_scriptrun_obj.starttime:
                                    end_time = current_scriptrun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S")
                                    start_time = current_scriptrun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S")
                                    delta_seconds = datetime.datetime.strptime(end_time,
                                                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                        start_time, '%Y-%m-%d %H:%M:%S')
                                    hour, minute, second = str(delta_seconds).split(":")

                                    delta_time = "{0}时{1}分{2}秒".format(hour, minute, second)

                                    script_el_dict_inner["rto"] = delta_time
                                else:
                                    script_el_dict_inner["rto"] = ""

                                state = current_scriptrun_obj.state
                                if state in state_dict.keys():
                                    script_el_dict_inner["state"] = state_dict[state]
                                else:
                                    script_el_dict_inner["state"] = ""

                                script_el_dict_inner["explain"] = current_scriptrun_obj.explain
                            else:
                                pass
                            script_list_inner.append(script_el_dict_inner)
                    inner_second_el_dict["script_list_inner"] = script_list_inner
                inner_step_list.append(inner_second_el_dict)
        second_el_dict['inner_step_list'] = inner_step_list
        step_info_list.append(second_el_dict)
    # return render(request, "pdf.html", locals())
    t = TemplateResponse(request, 'pdf.html',
                         {"step_info_list": step_info_list, "first_el_dict": first_el_dict, "ele_xml01": ele_xml01,
                          "ele_xml02": ele_xml02, "title_xml": title_xml, "abstract_xml": abstract_xml})
    t.render()
    current_path = os.getcwd()

    if sys.platform.startswith("win"):
        # 指定wkhtmltopdf运行程序路径
        wkhtmltopdf_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "process" + os.sep + "wkhtmltopdf" + os.sep + "bin" + os.sep + "wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    else:
        config = None

    options = {
        'page-size': 'A3',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    css_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "new" + os.sep + "css" + os.sep + "bootstrap.css"
    css = [r"{0}".format(css_path)]

    pdfkit.from_string(t.content.decode(encoding="utf-8"), r"falconstor.pdf", configuration=config,
                       options=options, css=css)

    the_file_name = "falconstor.pdf"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream; charset=unicode'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


@login_required
def falconstorsearch(request, funid):
    nowtime = datetime.datetime.now()
    endtime = nowtime.strftime("%Y-%m-%d")
    starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")).filter(pnode__pnode=None).order_by('-id')
    processname_list = []
    for process in all_processes:
        processname_list.append(process.name)

    state_dict = {
        "DONE": "已完成",
        "EDIT": "未执行",
        "RUN": "执行中",
        "ERROR": "执行失败",
        "IGNORE": "忽略",
        "STOP": "终止",
        "PLAN": "计划",
        "SIGN": "签到",
    }
    return render(request, "restore_search.html",
                  {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                   "processname_list": processname_list, "state_dict": state_dict,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def falconstorsearchdata(request):
    """
    演练查询
    :param request: starttime, endtime, runperson, runstate
    :return: starttime,endtime,createuser,state,process_id,processrun_id,runreason
    """
    result = []
    processname = request.GET.get('processname', '')
    runperson = request.GET.get('runperson', '')
    runstate = request.GET.get('runstate', '')
    startdate = request.GET.get('startdate', '')
    enddate = request.GET.get('enddate', '')
    start_time = datetime.datetime.strptime(startdate, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
    end_time = (datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
        seconds=1)).strftime('%Y-%m-%d %H:%M:%S')

    all_pruns = ProcessRun.objects.exclude(state__in=['9', 'REJECT']).filter(starttime__range=[start_time, end_time]).order_by('-starttime')

    if runperson:
        user_info = UserInfo.objects.filter(fullname=runperson)
        if user_info:
            user_info = user_info[0]
            runperson = user_info.user.username
        else:
            runperson = ""
        if processname != "" and runstate != "":
            all_pruns = all_pruns.filter(Q(pro_ins__process_name=processname) & Q(state=runstate) & Q(creatuser=runperson))
        if processname == "" and runstate != "":
            all_pruns = all_pruns.filter(Q(state=runstate) & Q(creatuser=runperson))
        if processname != "" and runstate == "":
            all_pruns = all_pruns.filter(Q(pro_ins__process_name=processname) & Q(creatuser=runperson))
        if processname == "" and runstate == "":
            all_pruns = all_pruns.filter(creatuser=runperson)
    else:
        if processname != "" and runstate != "":
            all_pruns = all_pruns.filter(Q(pro_ins__process_name=processname) & Q(state=runstate))
        if processname == "" and runstate != "":
            all_pruns = all_pruns.filter(state=runstate)
        if processname != "" and runstate == "":
            all_pruns = all_pruns.filter(pro_ins__process_name=processname)

    state_dict = {
        "DONE": "已完成",
        "EDIT": "未执行",
        "RUN": "执行中",
        "ERROR": "执行失败",
        "IGNORE": "忽略",
        "STOP": "终止",
        "PLAN": "计划",
        "REJECT": "取消",
        "SIGN": "签到",
        "CONTINUE": "继续",
        "": "",
    }

    rows = all_pruns.values(
        'starttime', 'endtime', 'creatuser', 'state', 'pro_ins__process_id', 'id', 'run_reason', 'pro_ins__process__name', 'pro_ins__process__url'
    )

    for row in rows:
        create_users = row['creatuser'] if row['creatuser'] else ""
        create_user_objs = User.objects.filter(username=create_users)
        create_user_fullname = create_user_objs[0].userinfo.fullname if create_user_objs else ""

        result.append({
            "starttime": row['starttime'].strftime('%Y-%m-%d %H:%M:%S') if row['starttime'] else "",
            "endtime": row['endtime'].strftime('%Y-%m-%d %H:%M:%S') if row['endtime'] else "",
            "createuser": create_user_fullname,
            "state": state_dict.get('{0}'.format(row['state']), ''),
            "process_id": row['pro_ins__process_id'] if row['pro_ins__process_id'] else "",
            "processrun_id": row['id'] if row['id'] else "",
            "run_reason": row['run_reason'][:20] if row['run_reason'] else "",
            "process_name": row['pro_ins__process__name'] if row['pro_ins__process__name'] else "",
            "process_url": row['pro_ins__process__url'] if row['pro_ins__process__url'] else ""
        })
    return HttpResponse(json.dumps({"data": result}))


@login_required
def tasksearch(request, funid):
    nowtime = datetime.datetime.now()
    endtime = nowtime.strftime("%Y-%m-%d")
    starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")).filter(pnode__pnode=None)
    processname_list = []
    for process in all_processes:
        processname_list.append(process.name)

    return render(request, "tasksearch.html",
                  {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                   "processname_list": processname_list, "pagefuns": getpagefuns(funid, request=request)})


@login_required
def tasksearchdata(request):
    result = []
    task_type = request.GET.get('task_type', '')
    has_finished = request.GET.get('has_finished', '')
    startdate = request.GET.get('startdate', '')
    enddate = request.GET.get('enddate', '')
    start_time = datetime.datetime.strptime(startdate, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
    end_time = (datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
        seconds=1)).strftime('%Y-%m-%d %H:%M:%S')

    all_ptasks = ProcessTask.objects.exclude(state='9').filter(starttime__range=[start_time, end_time]).order_by('-starttime')
    s_ptasks = all_ptasks.filter(type='INFO')

    if task_type != "" and has_finished != "":
        s_ptasks = all_ptasks.filter(Q(type=task_type) & Q(state=has_finished))
    if task_type == "" and has_finished != "":
        s_ptasks = all_ptasks.filter(Q(type='INFO') & Q(state=has_finished))
    if task_type != "" and has_finished == "":
        s_ptasks = all_ptasks.filter(type=task_type)
    rows = s_ptasks.values(
        'id', 'content', 'starttime', 'endtime', 'type', 'processrun_id', 'processrun__pro_ins__process__name', 'processrun__pro_ins__process__url', 'state'
    )

    type_dict = {
        "SIGN": "签到",
        "RUN": "操作",
        "ERROR": "错误",
        "": "",
    }

    has_finished_dict = {
        "1": "完成",
        "0": "未完成"
    }
    for task in rows:
        result.append({
            "task_id": task['id'],
            "task_content": task['content'],
            "starttime": task['starttime'].strftime('%Y-%m-%d %H:%M:%S') if task['starttime'] else "",
            "endtime": task['endtime'].strftime('%Y-%m-%d %H:%M:%S') if task['endtime'] else "",
            "type": type_dict["{0}".format(task['type'])] if task['type'] in type_dict.keys() else "",
            "processrun_id": task['processrun_id'] if task['processrun_id'] else "",
            "process_name": task['processrun__pro_ins__process__name'] if task['processrun__pro_ins__process__name'] else "",
            "process_url": task['processrun__pro_ins__process__url'] if task['processrun__pro_ins__process__url'] else "",
            "has_finished": has_finished_dict["{0}".format(task['state'])] if task['state'] in has_finished_dict.keys() else "",
        })
    return JsonResponse({"data": result})


def if_contains_sign(file_name):
    sign_string = '\/"*?<>'
    for i in sign_string:
        if i in file_name:
            return True
    return False


@login_required
def downloadlist(request, funid):
    errors = []
    if request.method == 'POST':
        file_remark = request.POST.get("file_remark", "")
        my_file = request.FILES.get("myfile", None)
        if not my_file:
            errors.append("请选择要导入的文件。")
        else:
            if if_contains_sign(my_file.name):
                errors.append(r"""请注意文件命名格式，'\/"*?<>'符号文件不允许上传。""")
            else:
                myfilepath = settings.BASE_DIR + os.sep + "faconstor" + os.sep + "upload" + os.sep + "knowledgefiles" + os.sep + my_file.name

                c_exist_model = KnowledgeFileDownload.objects.filter(file_name=my_file.name).exclude(state="9")

                if os.path.exists(myfilepath) or c_exist_model.exists():
                    errors.append("该文件已存在,请勿重复上传。")
                else:
                    with open(myfilepath, 'wb+') as f:
                        for chunk in my_file.chunks():  # 分块写入文件
                            f.write(chunk)

                    # 存入字段：备注，上传时间，上传人
                    c_file = KnowledgeFileDownload()
                    c_file.file_name = my_file.name
                    c_file.person = request.user.userinfo.fullname
                    c_file.remark = file_remark
                    c_file.upload_time = datetime.datetime.now()
                    c_file.save()

                    errors.append("导入成功。")
    return render(request, "downloadlist.html",
                  {'username': request.user.userinfo.fullname, "errors": errors,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def download_list_data(request):
    result = []
    c_files = KnowledgeFileDownload.objects.exclude(state="9")
    if c_files.exists():
        for file in c_files:
            result.append({
                "id": file.id,
                "name": file.person,
                "up_time": "{0:%Y-%m-%d %H:%M:%S}".format(file.upload_time),
                "remark": file.remark,
                "file_name": file.file_name,
            })

    return JsonResponse({
        "data": result
    })


@login_required
def knowledge_file_del(request):
    file_id = request.POST.get("id", "")
    assert int(file_id), "网页异常"

    c_file = KnowledgeFileDownload.objects.filter(id=file_id)
    if c_file.exists():
        c_file = c_file[0]
        c_file.delete()
        c_file_name = c_file.file_name
        the_file_name = settings.BASE_DIR + os.sep + "faconstor" + os.sep + "upload" + os.sep + "knowledgefiles" + os.sep + c_file_name
        if os.path.exists(the_file_name):
            os.remove(the_file_name)
        result = "删除成功。"
    else:
        result = "文件不存在，删除失败,请于管理员联系。"

    return JsonResponse({
        "data": result
    })


@login_required
def download(request):
    file_id = request.GET.get("file_id", "")
    assert int(file_id), "网页异常"
    c_file = KnowledgeFileDownload.objects.filter(id=file_id)
    if c_file.exists():
        c_file = c_file[0]
        c_file_name = c_file.file_name
    else:
        raise Http404()
    try:
        the_file_name = settings.BASE_DIR + os.sep + "faconstor" + os.sep + "upload" + os.sep + "knowledgefiles" + os.sep + c_file_name
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
            escape_uri_path(c_file_name))  # escape_uri_path()解决中文名文件
        return response
    except:
        return HttpResponseRedirect("/downloadlist")
