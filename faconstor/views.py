# coding:utf-8
import time
import datetime
import sys
import os
import json
import random
import uuid
import xlrd
import xlwt
from lxml import etree
import re
import pdfkit
import sys
import requests
from operator import itemgetter
import logging
from collections import OrderedDict
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils.timezone import utc
from django.utils.timezone import localtime
from django.shortcuts import render
from django.contrib import auth
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.http import StreamingHttpResponse
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum, Max
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils.encoding import escape_uri_path
from django.core.mail import send_mail
from django.forms.models import model_to_dict
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from djcelery.models import CrontabSchedule, PeriodicTask, IntervalSchedule

from faconstor.tasks import *
from faconstor.models import *
from .remote import ServerByPara
from TSDRM import settings
from .api import SQLApi

funlist = []

info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
        "lastlogin": 0}

walkthroughinfo = {}


def file_iterator(file_name, chunk_size=512):
    with open(file_name, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def getfun(myfunlist, fun):
    try:
        if (fun.pnode_id is not None):
            if fun not in myfunlist:
                childfun = {}
                if (fun.pnode_id != 1):
                    myfunlist = getfun(myfunlist, fun.pnode)
                myfunlist.append(fun)
    except:
        pass
    return myfunlist


def childfun(myfun, funid):
    mychildfun = []
    funs = myfun.children.order_by("sort").all()
    pisselected = False
    for fun in funs:
        if fun in funlist:
            isselected = False
            if str(fun.id) == funid:
                isselected = True
                pisselected = True
                mychildfun.append(
                    {"id": fun.id, "name": fun.name, "url": fun.url, "icon": fun.icon, "isselected": isselected,
                     "child": []})
            else:
                returnfuns = childfun(fun, funid)
                mychildfun.append({"id": fun.id, "name": fun.name, "url": fun.url, "icon": fun.icon,
                                   'isselected': returnfuns["isselected"], "child": returnfuns["fun"]})
                if returnfuns["isselected"]:
                    pisselected = returnfuns["isselected"]
    return {"fun": mychildfun, "isselected": pisselected}


def custom_time(time):
    """
    构造最新操作的时间
    :param time:
    :return:
    """
    time = time.replace(tzinfo=None)
    timenow = datetime.datetime.now()
    days = int((timenow - time).days)

    if days > 1095:
        time = "很久以前"
    else:
        if days > 730:
            time = "2年前"
        else:
            if days > 365:
                time = "1年前"
            else:
                if days > 182:
                    time = "半年前"
                else:
                    if days > 150:
                        time = "5月前"
                    else:
                        if days > 120:
                            time = "4月前"
                        else:
                            if days > 90:
                                time = "3月前"
                            else:
                                if days > 60:
                                    time = "2月前"
                                else:
                                    if days > 30:
                                        time = "1月前"
                                    else:
                                        if days >= 1:
                                            time = str(days) + "天前"
                                        else:
                                            hours = int((timenow - time).seconds / 3600)
                                            if hours >= 1:
                                                time = str(hours) + "小时"
                                            else:
                                                minutes = int((timenow - time).seconds / 60)
                                                if minutes >= 1:
                                                    time = str(minutes) + "分钟"
                                                else:
                                                    time = "刚刚"
    return time


def getpagefuns(funid, request=""):
    pagefuns = []
    mycurfun = {}
    message_task = []
    task_nums = 0

    for fun in funlist:
        if fun.pnode_id == 1:
            isselected = False
            if str(fun.id) == funid:
                isselected = True
                pagefuns.append(
                    {"id": fun.id, "name": fun.name, "url": fun.url, "icon": fun.icon, "isselected": isselected,
                     "child": []})
            else:
                returnfuns = childfun(fun, funid)
                pagefuns.append({"id": fun.id, "name": fun.name, "url": fun.url, "icon": fun.icon,
                                 "isselected": returnfuns["isselected"], "child": returnfuns["fun"]})
    curfun = Fun.objects.filter(id=int(funid))
    if len(curfun) > 0:
        myurl = curfun[0].url
        jsurl = curfun[0].url
        if len(myurl) > 0:
            myurl = myurl[:-1]
            jsurl = jsurl[:-1]
            if "falconstorswitch" in myurl:
                compile_obj = re.compile(r"/.*/")
                jsurl = compile_obj.findall(myurl)[0][:-1]
        mycurfun = {"id": curfun[0].id, "name": curfun[0].name, "url": myurl, "jsurl": jsurl}
    if request:
        # 右上角消息下拉菜单
        mygroup = []
        userinfo = request.user.userinfo
        guoups = userinfo.group.all()
        pop = False
        if len(guoups) > 0:
            for curguoup in guoups:
                mygroup.append(str(curguoup.id))
        allprosstasks = ProcessTask.objects.filter(
            Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(state="0").order_by(
            "-starttime").exclude(processrun__state="9").select_related("processrun", "processrun__process",
                                                                        "steprun__step")
        if len(allprosstasks) > 0:
            for task in allprosstasks:
                send_time = task.starttime
                process_name = task.processrun.process.name
                process_run_reason = task.processrun.run_reason
                task_id = task.id
                processrunid = task.processrun.id

                c_task_step_run = task.steprun
                if c_task_step_run:
                    address = c_task_step_run.step.remark
                    if not address:
                        address = ""
                else:
                    address = ""

                task_nums = len(allprosstasks)
                process_color = task.processrun.process.color
                process_url = task.processrun.process.url + "/" + str(task.processrun.id)
                time = task.starttime

                # 图标与颜色
                if task.type == "ERROR":
                    current_icon = "fa fa-exclamation-triangle"
                    current_color = "label-danger"
                elif task.type == "SIGN":
                    current_icon = "fa fa-user"
                    current_color = "label-warning"
                elif task.type == "RUN":
                    current_icon = "fa fa-bell-o"
                    current_color = "label-warning"
                else:
                    pass

                time = custom_time(time)

                message_task.append(
                    {"content": task.content, "time": time, "process_name": process_name, "address": address,
                     "task_color": current_color.strip(), "task_type": task.type, "task_extra": task.content,
                     "task_icon": current_icon, "process_color": process_color.strip(), "process_url": process_url,
                     "pop": True if task.type == "SIGN" else False, "task_id": task_id,
                     "send_time": send_time.strftime("%Y-%m-%d %H:%M:%S"),
                     "processrunid": processrunid, "process_run_reason": process_run_reason,
                     "group_name": guoups[0].name})
    return {"pagefuns": pagefuns, "curfun": mycurfun, "message_task": message_task, "task_nums": task_nums}


@login_required
def test(request):
    errors = []
    return render(request, 'test.html',
                  {'username': request.user.userinfo.fullname, "errors": errors})


@login_required
def processindex(request, processrun_id):
    errors = []
    # processrun_id = request.GET.get("p_run_id", "")
    s_tag = request.GET.get("s", "")
    # exclude
    c_process_run = ProcessRun.objects.filter(id=processrun_id).select_related("process")
    if c_process_run.exists():
        process_url = c_process_run[0].process.url
        process_name = c_process_run[0].process.name
        process_id = c_process_run[0].process.id
    else:
        raise Http404()
    return render(request, 'processindex.html',
                  {'username': request.user.userinfo.fullname, "errors": errors, "processrun_id": processrun_id,
                   "process_url": process_url, "process_name": process_name, "process_id": process_id,
                   "s_tag": s_tag})


@login_required
def walkthroughindex(request, walkthrough_id):
    errors = []
    # processrun_id = request.GET.get("p_run_id", "")
    s_tag = request.GET.get("s", "")
    # exclude
    global walkthroughinfo
    walkthroughinfo = {}
    walkthrough = Walkthrough.objects.filter(id=walkthrough_id)
    if walkthrough.exists():
        walkthrough_name = walkthrough[0].name
    else:
        raise Http404()
    return render(request, 'walkthroughindex.html',
                  {'username': request.user.userinfo.fullname, "errors": errors, "walkthrough_id": walkthrough_id,
                   "walkthrough_name": walkthrough_name,
                   "s_tag": s_tag})


@login_required
def get_process_index_data(request):
    processrun_id = request.POST.get("p_run_id", "")

    current_processruns = ProcessRun.objects.filter(id=int(processrun_id)).select_related("process")

    if current_processruns:
        current_processrun = current_processruns[0]

        # 当前流程状态
        c_process_run_state = current_processrun.state
        name = current_processrun.process.name
        starttime = current_processrun.starttime
        endtime = current_processrun.endtime
        rtoendtime = ""

        state = current_processrun.state
        percent = 0

        process_id = current_processrun.process_id

        # 正确顺序的父级Step
        all_pnode_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=None).order_by(
            "sort")
        correct_step_id_list = []
        if all_pnode_steps:
            for pnode_step in all_pnode_steps:
                pnode_step_id = pnode_step.id
                correct_step_id_list.append(pnode_step_id)
        else:
            raise Http404()

        # 正确顺序的父级StepRun
        correct_step_run_list = []
        for step_id in correct_step_id_list:
            current_step_run = StepRun.objects.filter(step_id=step_id).filter(
                processrun_id=processrun_id).select_related("step")
            if current_step_run.exists():
                current_step_run = current_step_run[0]
                correct_step_run_list.append(current_step_run)

        # 构造当前流程步骤info
        steps = []
        rtostate = "RUN"

        if correct_step_run_list:
            c_step_index = 0
            # 流程运行中的rtostate
            if c_process_run_state != "DONE":
                if c_process_run_state == "ERROR":
                    rtostate = "RUN"
                else:
                    c_state = False
                    for num, c_step_run in enumerate(correct_step_run_list):
                        c_rto_count_in = c_step_run.step.rto_count_in
                        if c_rto_count_in == "0" and c_step_run.state in ["CONFIRM", "DONE"]:
                            c_state = True
                            rtostate = "DONE"
                            c_step_index = num
                            break

                    if c_state:
                        # 表示需要计入rto的步骤已经完成
                        if c_step_index > 0 and rtostate == "DONE":
                            pre_step_index = c_step_index - 1
                            rtoendtime = correct_step_run_list[pre_step_index].endtime.strftime('%Y-%m-%d %H:%M:%S')
            # 流程结束后的rtostate
            else:
                for num, c_step_run in enumerate(correct_step_run_list):
                    c_rto_count_in = c_step_run.step.rto_count_in
                    if c_rto_count_in == "0" and c_step_run.state == "DONE":
                        rtostate = "DONE"
                        c_step_index = num
                        break

                if c_step_index > 0 and rtostate == "DONE":
                    pre_step_index = c_step_index - 1
                    rtoendtime = correct_step_run_list[pre_step_index].endtime.strftime('%Y-%m-%d %H:%M:%S')

            if_has_run = False
            if_has_index = 0
            for num, c_step_run in enumerate(correct_step_run_list):
                num += 1
                if c_step_run.state not in ["DONE", "STOP", "EDIT"]:
                    if_has_run = True
                    break
                elif c_step_run.state == "DONE":
                    if_has_index = num

            for num, c_step_run in enumerate(correct_step_run_list):
                num += 1
                # 流程结束后的当前步骤
                if c_process_run_state == "DONE":
                    if num == len(correct_step_run_list):
                        c_step_run_type = "cur"
                    else:
                        c_step_run_type = ""
                # 流程运行中的当前步骤
                else:
                    if c_step_run.state not in ["DONE", "STOP", "EDIT"]:
                        c_step_run_type = "cur"
                    else:
                        # 这里还要加一个没有RUN的判断
                        c_step_run_type = ""

                if not if_has_run and num == if_has_index:
                    c_step_run_type = "cur"

                c_step_id = c_step_run.step.id
                c_inner_step_runs = StepRun.objects.filter(step__pnode_id=c_step_id).filter(step__state__in=["9"])

                # 未完成
                all_steps = c_step_run.step.children.exclude(state="9")
                all_done_step_list = []
                for step in all_steps:
                    step_id = step.id
                    done_step_run = StepRun.objects.filter(step_id=step_id).filter(
                        processrun_id=processrun_id).filter(state="DONE")
                    if done_step_run.exists():
                        all_done_step_list.append(done_step_run[0])

                if all_done_step_list:
                    inner_step_run_percent = "%2d" % (len(all_done_step_list) / len(all_steps) * 100)
                else:
                    inner_step_run_percent = 0

                if c_step_run.state in ["DONE", "STOP"]:
                    inner_step_run_percent = 100

                start_time = c_step_run.starttime
                end_time = c_step_run.endtime

                delta_time = 0
                if c_step_run.step.children.all().exclude(
                        state="9").count() == 0 and c_step_run.verifyitemsrun_set.all().count() == 0 and c_step_run.scriptrun_set.all().exists():
                    # 用于判断 没有子步骤，不需要确认，有脚本的步骤
                    now_time = datetime.datetime.now()
                    if not end_time and start_time:
                        delta_time = (now_time - start_time)
                        if delta_time:
                            delta_time = "%.f" % delta_time.total_seconds()
                        else:
                            delta_time = 0
                    c_tag = "yes"
                else:
                    c_tag = "no"
                c_step_run_dict = {
                    "name": c_step_run.step.name,
                    "state": c_step_run.state if c_step_run.state else "",
                    "starttime": starttime.strftime('%Y-%m-%d %H:%M:%S') if starttime else None,
                    "endtime": endtime.strftime('%Y-%m-%d %H:%M:%S') if endtime else None,
                    "percent": inner_step_run_percent,
                    "type": c_step_run_type,
                    "delta_time": delta_time,
                    "c_tag": c_tag,
                }
                steps.append(c_step_run_dict)

        done_step_run = current_processrun.steprun_set.filter(state="DONE")
        if done_step_run.exists():
            done_num = len(done_step_run)
        else:
            done_num = 0

        # 构造展示步骤
        process_rate = "%02d" % (done_num / len(current_processrun.steprun_set.all()) * 100)

        if current_processrun.state == "SIGN":
            rtostate = "DONE"
            rtoendtime = current_processrun.starttime.strftime('%Y-%m-%d %H:%M:%S')
        current_time = datetime.datetime.now()
        c_step_run_data = {
            "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "name": name,
            "starttime": starttime.strftime('%Y-%m-%d %H:%M:%S') if starttime else "",
            "rtoendtime": rtoendtime,
            "endtime": endtime.strftime('%Y-%m-%d %H:%M:%S') if endtime else "",
            "state": state,
            "rtostate": rtostate,
            "percent": process_rate,
            "steps": steps
        }
    else:
        c_step_run_data = {}
    # print("c_step_run_data", c_step_run_data)
    return JsonResponse(c_step_run_data)


@login_required
def get_walkthrough_index_data(request):
    walkthrough_id = request.POST.get("walkthrough_id", "")
    walkthroughs = Walkthrough.objects.filter(id=walkthrough_id)
    if walkthroughs:
        walkthrough = walkthroughs[0]
        walkthrough_name = walkthrough.name
        walkthrough_state = walkthrough.state
        walkthrough_starttime = walkthrough.starttime
        walkthrough_endtime = walkthrough.endtime
        processrunes = walkthrough.processrun_set.exclude(state="9").exclude(state='REJECT')
        cur_processruns = []
        processrunid = []
        showtasks = []
        for processrun in processrunes:
            processrunid.append(processrun.id)
            processrun_id = processrun.id
            current_processruns = ProcessRun.objects.filter(id=int(processrun_id)).select_related("process")

            if current_processruns:
                current_processrun = current_processruns[0]

                # 当前流程状态
                c_process_run_state = current_processrun.state
                name = current_processrun.process.name
                starttime = current_processrun.starttime
                endtime = current_processrun.endtime
                walkthroughstate = current_processrun.walkthroughstate
                rtoendtime = ""
                state = current_processrun.state
                percent = 0

                process_id = current_processrun.process_id
                # 正确顺序的父级Step
                all_pnode_steps = Step.objects.exclude(state="9").filter(process_id=process_id,
                                                                         pnode_id=None).exclude(
                    rto_count_in='0').order_by(
                    "sort")
                correct_step_id_list = []
                if all_pnode_steps:
                    for pnode_step in all_pnode_steps:
                        pnode_step_id = pnode_step.id
                        correct_step_id_list.append(pnode_step_id)
                    # 正确顺序的父级StepRun
                    correct_step_run_list = []
                    for step_id in correct_step_id_list:
                        current_step_run = StepRun.objects.filter(step_id=step_id).filter(
                            processrun_id=processrun_id).select_related("step")
                        if current_step_run.exists():
                            current_step_run = current_step_run[0]
                            correct_step_run_list.append(current_step_run)
                    # 构造当前流程步骤info
                    steps = []
                    rtostate = "RUN"

                    if correct_step_run_list:
                        c_step_index = 0
                        # 流程运行中的rtostate
                        if c_process_run_state != "DONE":
                            if c_process_run_state == "ERROR":
                                rtostate = "RUN"
                            else:
                                c_state = False
                                for num, c_step_run in enumerate(correct_step_run_list):
                                    c_rto_count_in = c_step_run.step.rto_count_in
                                    if c_rto_count_in == "0" and c_step_run.state in ["CONFIRM", "DONE"]:
                                        c_state = True
                                        rtostate = "DONE"
                                        c_step_index = num
                                        break

                                if c_state:
                                    # 表示需要计入rto的步骤已经完成
                                    if c_step_index > 0 and rtostate == "DONE":
                                        pre_step_index = c_step_index - 1
                                        rtoendtime = correct_step_run_list[pre_step_index].endtime.strftime(
                                            '%Y-%m-%d %H:%M:%S')
                        # 流程结束后的rtostate
                        else:
                            for num, c_step_run in enumerate(correct_step_run_list):
                                c_rto_count_in = c_step_run.step.rto_count_in
                                if c_rto_count_in == "0" and c_step_run.state == "DONE":
                                    rtostate = "DONE"
                                    c_step_index = num
                                    break

                            if c_step_index > 0 and rtostate == "DONE":
                                pre_step_index = c_step_index - 1
                                rtoendtime = correct_step_run_list[pre_step_index].endtime.strftime(
                                    '%Y-%m-%d %H:%M:%S')

                        if_has_run = False
                        if_has_index = 0
                        for num, c_step_run in enumerate(correct_step_run_list):
                            num += 1
                            if c_step_run.state not in ["DONE", "STOP", "EDIT"]:
                                if_has_run = True
                                break
                            elif c_step_run.state == "DONE":
                                if_has_index = num

                        for num, c_step_run in enumerate(correct_step_run_list):
                            num += 1
                            # 流程结束后的当前步骤
                            if c_process_run_state == "DONE":
                                if num == len(correct_step_run_list):
                                    c_step_run_type = "cur"
                                else:
                                    c_step_run_type = ""
                            # 流程运行中的当前步骤
                            else:
                                if c_step_run.state not in ["DONE", "STOP", "EDIT"]:
                                    c_step_run_type = "cur"
                                else:
                                    # 这里还要加一个没有RUN的判断
                                    c_step_run_type = ""

                            if not if_has_run and num == if_has_index:
                                c_step_run_type = "cur"

                            c_step_id = c_step_run.step.id
                            c_inner_step_runs = StepRun.objects.filter(step__pnode_id=c_step_id).filter(
                                step__state__in=["9"])

                            # 未完成
                            all_steps = c_step_run.step.children.exclude(state="9")
                            all_done_step_list = []
                            for step in all_steps:
                                step_id = step.id
                                done_step_run = StepRun.objects.filter(step_id=step_id).filter(
                                    processrun_id=processrun_id).filter(state="DONE")
                                if done_step_run.exists():
                                    all_done_step_list.append(done_step_run[0])

                            if all_done_step_list:
                                inner_step_run_percent = "%2d" % (len(all_done_step_list) / len(all_steps) * 100)
                            else:
                                inner_step_run_percent = 0

                            if c_step_run.state in ["DONE", "STOP"]:
                                inner_step_run_percent = 100

                            start_time = c_step_run.starttime
                            end_time = c_step_run.endtime

                            delta_time = 0
                            if c_step_run.step.children.all().exclude(
                                    state="9").count() == 0 and c_step_run.verifyitemsrun_set.all().count() == 0 and c_step_run.scriptrun_set.all().exists():
                                # 用于判断 没有子步骤，不需要确认，有脚本的步骤
                                now_time = datetime.datetime.now()
                                if not end_time and start_time:
                                    delta_time = (now_time - start_time)
                                    if delta_time:
                                        delta_time = "%.f" % delta_time.total_seconds()
                                    else:
                                        delta_time = 0
                                c_tag = "yes"
                            else:
                                c_tag = "no"
                            c_step_run_dict = {
                                "name": c_step_run.step.name,
                                "state": c_step_run.state if c_step_run.state else "",
                                "starttime": starttime.strftime('%Y-%m-%d %H:%M:%S') if starttime else None,
                                "endtime": endtime.strftime('%Y-%m-%d %H:%M:%S') if endtime else None,
                                "percent": inner_step_run_percent,
                                "type": c_step_run_type,
                                "delta_time": delta_time,
                                "c_tag": c_tag,
                            }
                            steps.append(c_step_run_dict)

                    done_step_run = current_processrun.steprun_set.filter(state="DONE")
                    if done_step_run.exists():
                        done_num = len(done_step_run)
                    else:
                        done_num = 0

                    # 构造展示步骤
                    process_rate = "%02d" % (done_num / len(current_processrun.steprun_set.all()) * 100)
                    isConfirm = "0"
                    confirmStepruns = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id,
                                                                                state='CONFIRM')
                    if len(confirmStepruns) > 0:
                        isConfirm = "1"

                    if current_processrun.state == "SIGN":
                        rtostate = "DONE"
                        rtoendtime = current_processrun.starttime.strftime('%Y-%m-%d %H:%M:%S')
                    cur_processruns.append({
                        "processrun_id": processrun_id,
                        "process_id": process_id,
                        "processurl": current_processrun.process.url,
                        "name": name,
                        "starttime": starttime.strftime('%Y-%m-%d %H:%M:%S') if starttime else "",
                        "rtoendtime": rtoendtime,
                        "endtime": endtime.strftime('%Y-%m-%d %H:%M:%S') if endtime else "",
                        "state": state,
                        "rtostate": rtostate,
                        "percent": process_rate,
                        "walkthroughstate": walkthroughstate,
                        "isConfirm": isConfirm,
                        "steps": steps
                    })

        current_time = datetime.datetime.now()
        tasks = ProcessTask.objects.filter(type='info').filter(
            Q(processrun_id__in=processrunid) | Q(walkthrough_id=walkthroughs[0].id)).exclude(state='9').exclude(
            content="创建演练计划。").exclude(content="修改演练计划。").exclude(content="创建流程计划。").exclude(
            content="修改流程计划。").exclude(content="演练启动。")
        for task in tasks:
            taskname = ""
            if task.processrun is not None:
                taskname = task.processrun.process.name.replace("系统", "")
            taskcontent = taskname + task.content.replace("脚本", "").replace("步骤", "")
            isintasks = False
            for oldtask in showtasks:
                if taskcontent == oldtask["taskcontent"]:
                    isintasks = True
            if not isintasks:
                showtasks.append({
                    "taskid": task.id,
                    "taskname": taskname,
                    "taskcontent": taskcontent,
                    "tasktime": task.starttime.strftime('%Y-%m-%d %H:%M:%S') if task.starttime else "",
                })
        c_walkthrough_run_data = {
            "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "walkthrough_name": walkthrough_name,
            "walkthrough_state": walkthrough_state,
            "walkthrough_starttime": walkthrough_starttime.strftime(
                '%Y-%m-%d %H:%M:%S') if walkthrough_starttime else "",
            "walkthrough_endtime": walkthrough_endtime.strftime('%Y-%m-%d %H:%M:%S') if walkthrough_endtime else "",
            "processruns": cur_processruns,
            "showtasks": showtasks,
        }
        global walkthroughinfo
        oldwalkthroughinfo = walkthroughinfo
        walkthroughinfo = c_walkthrough_run_data
        c_walkthrough_run_data["oldwalkthroughinfo"] = oldwalkthroughinfo
    else:
        c_walkthrough_run_data = {}
    return JsonResponse(c_walkthrough_run_data)


@login_required
def walkthrough_run_invited(request):
    result = {}

    walkthrough_id = request.POST.get('walkthrough_id', '')

    current_walkthrough_run = Walkthrough.objects.filter(id=walkthrough_id)

    if current_walkthrough_run:
        current_walkthrough_run = current_walkthrough_run[0]

        if current_walkthrough_run.state == "RUN":
            result["res"] = '请勿重复启动该演练。'
        else:
            current_process_run = current_walkthrough_run.processrun_set.filter(state="PLAN")
            if current_process_run:
                current_process_run = current_process_run[0]
                current_process_run.starttime = datetime.datetime.now()
                current_process_run.state = "RUN"
                current_process_run.walkthroughstate = "RUN"
                current_process_run.DataSet_id = 89
                current_process_run.save()

                process = Process.objects.filter(id=current_process_run.process_id).exclude(state="9").exclude(
                    Q(type=None) | Q(type=""))

                allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                    "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                    # 将当前流程改成SIGN
                    c_process_run_id = current_process_run.id
                    c_process_run = ProcessRun.objects.filter(id=c_process_run_id)
                    if c_process_run:
                        c_process_run = c_process_run[0]
                        c_process_run.state = "SIGN"
                        c_process_run.walkthroughstate = "RUN"
                        c_process_run.save()
                    for group in allgroup:
                        try:
                            signgroup = Group.objects.get(id=int(group["group"]))
                            groupname = signgroup.name
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = current_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = request.user.username
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
                        myprocesstask.senduser = request.user.username
                        myprocesstask.content = "流程启动。"
                        myprocesstask.save()

                        exec_process.delay(current_process_run.id)
                mywalkthroughtask = ProcessTask()
                mywalkthroughtask.walkthrough = current_walkthrough_run
                mywalkthroughtask.starttime = datetime.datetime.now()
                mywalkthroughtask.senduser = request.user.username
                mywalkthroughtask.type = "INFO"
                mywalkthroughtask.logtype = "START"
                mywalkthroughtask.state = "1"
                mywalkthroughtask.content = "演练启动。"
                mywalkthroughtask.save()

                current_walkthrough_run.starttime = datetime.datetime.now()
                current_walkthrough_run.state = "RUN"
                current_walkthrough_run.endtime = None
                current_walkthrough_run.save()
                result["res"] = "启动成功。"
            else:
                result["res"] = '演练启动异常，该演练未选择任何演练系统。'
    else:
        result["res"] = '演练启动异常，请联系客服。'

    return HttpResponse(json.dumps(result))


def custom_walkthrough_info(walkthrough_id):
    show_result_dict = {}

    try:
        cur_walkthrough = Walkthrough.objects.get(id=walkthrough_id)
    except Walkthrough.DoesNotExist as e:
        return {}
    else:
        # 演练时间
        show_result_dict["walkthrough_starttime"] = "{:%Y-%m-%d}".format(
            cur_walkthrough.starttime) if cur_walkthrough.starttime else ""

        # 演练原因
        show_result_dict["purpose"] = cur_walkthrough.purpose

        # 用户组信息
        all_groups = Group.objects.exclude(state="9")
        total_list = []
        if all_groups:
            for group in all_groups:
                all_group_dict = {}
                current_group_users = group.userinfo_set.exclude(state="9", pnode=None).filter(type="user")
                if current_group_users:
                    all_group_dict["group"] = group.name

                    current_users_and_departments = []
                    for user in current_group_users:
                        inner_dict = {}
                        inner_dict["fullname"] = user.fullname
                        inner_dict["depart_name"] = user.pnode.fullname if user.pnode else ""
                        current_users_and_departments.append(inner_dict)
                    all_group_dict["current_users_and_departments"] = current_users_and_departments
                    total_list.append(all_group_dict)
        show_result_dict["total_list"] = total_list

        process_info_list = []

        all_process_runs = cur_walkthrough.processrun_set.exclude(state="9")

        all_process_name = ""
        for current_processrun in all_process_runs:
            process_info = {}

            process_id = current_processrun.process.id
            processrun_id = current_processrun.id
            process_name = current_processrun.process.name if current_processrun else ""
            # processrun_time = current_processrun.starttime.strftime("%Y-%m-%d")
            all_process_name += process_name + ","
            # 父级
            step_info_list = []
            pnode_steplist = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
                pnode_id=None)

            for num, pstep in enumerate(pnode_steplist):
                second_el_dict = dict()
                step_name = pstep.name
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
                        second_el_dict["start_time"] = pnode_steprun.starttime.strftime(
                            "%Y-%m-%d %H:%M:%S") if pnode_steprun.starttime else ""
                        second_el_dict["end_time"] = pnode_steprun.endtime.strftime(
                            "%Y-%m-%d %H:%M:%S") if pnode_steprun.endtime else ""

                        if pnode_steprun.endtime and pnode_steprun.starttime:
                            end_time = pnode_steprun.endtime.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            start_time = pnode_steprun.starttime.strftime(
                                "%Y-%m-%d %H:%M:%S")
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
                    if users:
                        operator = users[0].userinfo.fullname
                        second_el_dict["operator"] = operator
                    else:
                        second_el_dict["operator"] = ""
                except:
                    second_el_dict["operator"] = ""

                p_id = pstep.id
                inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
                    pnode_id=p_id)

                # 子级
                inner_step_list = []
                if inner_steps:
                    for num, step in enumerate(inner_steps):
                        inner_second_el_dict = dict()
                        step_name = step.name
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
                                inner_second_el_dict["start_time"] = steprun_obj.starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if \
                                    steprun_obj.starttime else ""
                                inner_second_el_dict["end_time"] = steprun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S") if \
                                    steprun_obj.endtime else ""

                                if steprun_obj.endtime and steprun_obj.starttime:
                                    end_time = steprun_obj.endtime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    start_time = steprun_obj.starttime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    delta_seconds = datetime.datetime.strptime(end_time,
                                                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                        start_time, '%Y-%m-%d %H:%M:%S')
                                    hour, minute, second = str(
                                        delta_seconds).split(":")
                                    delta_time = "{0}时{1}分{2}秒".format(
                                        hour, minute, second)

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

                        inner_step_list.append(inner_second_el_dict)
                second_el_dict['inner_step_list'] = inner_step_list
                step_info_list.append(second_el_dict)

            process_info["step_info_list"] = step_info_list

            all_step_runs = current_processrun.steprun_set.exclude(state="9").exclude(step__rto_count_in="0").filter(
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
            all_inner_step_runs = current_processrun.steprun_set.exclude(state="9").filter(
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
            process_info["rto"] = "%d时%02d分%02d秒" % (h, m, s)

            # process_name
            process_info["process_name"] = process_name
            # processrun_time
            # show_result_dict["processrun_time"] = processrun_time

            # 项目起始时间，结束时间，RTO
            process_info["start_time"] = current_processrun.starttime.strftime(
                "%Y-%m-%d %H:%M:%S") if current_processrun.starttime else ""
            process_info["end_time"] = current_processrun.endtime.strftime(
                "%Y-%m-%d %H:%M:%S") if current_processrun.endtime else ""

            # process_length
            process_length = 0
            for step in step_info_list:
                inner_step_length = len(step["inner_step_list"])
                if inner_step_length:
                    process_length += inner_step_length
                else:
                    process_length += 1

            process_info["process_length"] = process_length
            process_info["processrun_id"] = processrun_id
            process_info_list.append(process_info)
        # return render(request, "walkthroughpdf.html", {"show_result_dict": json.dumps(show_result_dict)})

        show_result_dict["process_info_list"] = process_info_list

        # 所有演练项目
        if all_process_name.endswith(","):
            all_process_name = all_process_name[:-1]
        show_result_dict["all_process_name"] = all_process_name
        return show_result_dict


@login_required
def walkthrough_pdf(request):
    walkthrough_id = request.GET.get("walkthrough_id", "")
    # processrun_id = 916
    try:
        walkthrough_id = int(walkthrough_id)
    except ValueError as e:
        print(e)
        raise Http404()

    show_result_dict = custom_walkthrough_info(walkthrough_id)
    if not show_result_dict:
        raise Http404()

    current_path = os.getcwd()

    jQuery_path = os.path.join(os.path.join(
        os.path.join(os.path.join(os.path.join(os.path.join(current_path, "faconstor"), "static"), "assets"), "global"),
        "plugins"), "jquery.min.js").replace("\\", "/")
    walkthroughpdf_js_path = os.path.join(
        os.path.join(os.path.join(os.path.join(current_path, "faconstor"), "static"), "myjs"),
        "walkthroughpdf.js").replace("\\", "/")

    # return render(request, 'walkthroughpdf.html', {"show_result_dict": json.dumps(show_result_dict)})
    t = TemplateResponse(request, 'walkthroughpdf.html',
                         {"show_result_dict": json.dumps(show_result_dict), "jQuery_path": jQuery_path,
                          "walkthroughpdf_js_path": walkthroughpdf_js_path})
    t.render()

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
    css_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "new" + os.sep + "css"
    css_01 = css_path + os.sep + "bootstrap.css"
    css_03 = css_path + os.sep + "icon.css"
    css_05 = css_path + os.sep + "app.css"
    css_06 = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "assets" + os.sep + "global" + os.sep + "css" + os.sep + "components.css"

    css = [r"{0}".format(mycss) for mycss in [css_01, css_03, css_05, css_06]]
    pdfkit.from_string(t.content.decode(encoding="utf-8"), r"report.pdf", configuration=config, options=options,
                       css=css)
    the_file_name = "report.pdf"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream; charset=unicode'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


@login_required
def get_walkthrough_info(request):
    walkthrough_id = request.POST.get("walkthrough_id", "")
    try:
        walkthrough_id = int(walkthrough_id)
    except ValueError as e:
        print(e)
        return JsonResponse({})
    show_result_dict = custom_walkthrough_info(walkthrough_id)
    return JsonResponse(show_result_dict)


@login_required
def get_server_time_very_second(request):
    current_time = datetime.datetime.now()
    return JsonResponse({"current_time": current_time.strftime('%Y-%m-%d %H:%M:%S')})


def custom_c_color(task_type, task_state, task_logtype):
    """
    构造图标与颜色
    :param task_type:
    :param task_state:
    :param task_logtype:
    :return: current_icon, current_color
    """
    if task_type == "ERROR":
        current_icon = "fa fa-exclamation-triangle"
        if task_state == "0":
            current_color = "label-danger"
        if task_state == "1":
            current_color = "label-default"
    elif task_type == "SIGN":
        current_icon = "fa fa-user"
        if task_state == "0":
            current_color = "label-warning"
        if task_state == "1":
            current_color = "label-info"
    elif task_type == "RUN":
        current_icon = "fa fa-bell-o"
        if task_state == "0":
            current_color = "label-warning"
        if task_state == "1":
            current_color = "label-info"
    else:
        current_color = "label-success"
        if task_logtype == "START":
            current_icon = "fa fa-power-off"
        elif task_logtype == "START":
            current_icon = "fa fa-power-off"
        elif task_logtype == "STEP":
            current_icon = "fa fa-cog"
        elif task_logtype == "SCRIPT":
            current_icon = "fa fa-cog"
        elif task_logtype == "STOP":
            current_icon = "fa fa-stop"
        elif task_logtype == "CONTINUE":
            current_icon = "fa fa-play"
        elif task_logtype == "IGNORE":
            current_icon = "fa fa-share"
        elif task_logtype == "START":
            current_icon = "fa fa-power-off"
        elif task_logtype == "END":
            current_icon = "fa fa-lock"
        else:
            current_icon = "fa fa-info-circle"
    return current_icon, current_color


def get_c_process_run_tasks(current_processrun_id):
    """
    获取当前系统任务
    :return:
    """
    # 当前系统任务
    current_process_task_info = []

    cursor = connection.cursor()
    cursor.execute("""
    select t.starttime, t.content, t.type, t.state, t.logtype from faconstor_processtask as t where t.processrun_id = '{0}' order by t.starttime desc;
    """.format(current_processrun_id))
    rows = cursor.fetchall()
    if len(rows) > 0:
        for task in rows:
            time = task[0]
            content = task[1]
            task_type = task[2]
            task_state = task[3]
            task_logtype = task[4]

            # 图标与颜色
            current_icon, current_color = custom_c_color(task_type, task_state, task_logtype)

            time = custom_time(time)

            current_process_task_info.append(
                {"content": content, "time": time, "task_color": current_color,
                 "task_icon": current_icon})
    return current_process_task_info


@login_required
def index(request, funid):
    global funlist
    funlist = []
    if request.user.is_superuser == 1:
        allfunlist = Fun.objects.all()
        for fun in allfunlist:
            funlist.append(fun)
    else:
        cursor = connection.cursor()
        cursor.execute(
            "select faconstor_fun.id from faconstor_group,faconstor_fun,faconstor_userinfo,faconstor_userinfo_group,faconstor_group_fun "
            "where faconstor_group.id=faconstor_userinfo_group.group_id and faconstor_group.id=faconstor_group_fun.group_id and "
            "faconstor_group_fun.fun_id=faconstor_fun.id and faconstor_userinfo.id=faconstor_userinfo_group.userinfo_id and userinfo_id= "
            + str(request.user.userinfo.id) + " order by faconstor_fun.sort"
        )

        rows = cursor.fetchall()
        for row in rows:
            try:
                fun = Fun.objects.get(id=row[0])
                funlist = getfun(funlist, fun)
            except:
                pass
    for index, value in enumerate(funlist):
        if value.sort is None:
            value.sort = 0
    funlist = sorted(funlist, key=lambda fun: fun.sort)
    # 最新操作
    alltask = []
    cursor = connection.cursor()
    cursor.execute("""
    select t.starttime, t.content, t.type, t.state, t.logtype, p.name, p.color from faconstor_processtask as t left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where r.state!='9' order by t.starttime desc;
    """)
    rows = cursor.fetchall()

    if len(rows) > 0:
        for task in rows:
            time = task[0]
            content = task[1]
            task_type = task[2]
            task_state = task[3]
            task_logtype = task[4]
            process_name = task[5]
            process_color = task[6]

            # 图标与颜色
            current_icon, current_color = custom_c_color(task_type, task_state, task_logtype)

            time = custom_time(time)

            alltask.append(
                {"content": content, "time": time, "process_name": process_name, "task_color": current_color,
                 "task_icon": current_icon, "process_color": process_color})
            if len(alltask) >= 50:
                break
    # 成功率，恢复次数，平均RTO，最新切换
    all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="STOP"))
    successful_processruns = ProcessRun.objects.filter(state="DONE")
    processrun_times_obj = ProcessRun.objects.exclude(state__in=["RUN", "REJECT"]).exclude(state="9")

    success_rate = "%.0f" % (len(successful_processruns) / len(
        all_processrun_objs) * 100) if all_processrun_objs and successful_processruns else 0
    last_processrun_time = successful_processruns.last().starttime if successful_processruns else ""
    all_processruns = len(processrun_times_obj) if processrun_times_obj else 0

    if successful_processruns:
        rto_sum_seconds = 0

        for processrun in successful_processruns:
            all_step_runs = processrun.steprun_set.exclude(state="9").exclude(step__rto_count_in="0").filter(
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
            rto_sum_seconds += step_rto

            # 扣除子级步骤中可能的rto_count_in的时间
            all_inner_step_runs = processrun.steprun_set.exclude(state="9").filter(step__rto_count_in="0").exclude(
                step__pnode=None).exclude(step__pnode__rto_count_in="0")
            inner_rto_not_count_in = 0
            if all_inner_step_runs:
                for inner_step_run in all_inner_step_runs:
                    end_time = inner_step_run.endtime
                    start_time = inner_step_run.starttime
                    if end_time and start_time:
                        delta_time = (end_time - start_time)
                        rto = delta_time.total_seconds()
                        inner_rto_not_count_in += rto
            rto_sum_seconds -= inner_rto_not_count_in

        m, s = divmod(rto_sum_seconds / len(successful_processruns), 60)
        h, m = divmod(m, 60)
        average_rto = "%d时%02d分%02d秒" % (h, m, s)
    else:
        average_rto = "00时00分00秒"

    # 正在切换:start_time, delta_time, current_step, current_operator， current_process_name, all_steps
    current_processruns = ProcessRun.objects.exclude(state__in=["PLAN", "DONE", "STOP", "REJECT"]).exclude(
        state="9").select_related("process")
    curren_processrun_info_list = []
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

    process_rate = "0"
    if current_processruns:
        for current_processrun in current_processruns:
            current_processrun_dict = {}
            start_time_strftime = ""
            current_delta_time = ""
            current_step_name = ""
            current_process_name = ""
            current_step_index = ""
            all_steps = []
            group_name = ""
            users = ""
            process_id = current_processrun.process_id
            current_process_name = current_processrun.process.name
            start_time = current_processrun.starttime.replace(tzinfo=None)
            start_time_strftime = start_time.strftime('%Y-%m-%d %H:%M:%S')
            current_time = datetime.datetime.now()
            current_delta_time = (current_time - start_time).total_seconds()
            m, s = divmod(current_delta_time, 60)
            h, m = divmod(m, 60)
            current_delta_time = "%d时%02d分%02d秒" % (h, m, s)

            current_processrun_id = current_processrun.id

            # 进程url
            processrun_url = current_processrun.process.url + "/" + str(current_processrun_id)

            # 当前系统任务
            current_process_task_info = get_c_process_run_tasks(current_processrun.id)

            current_processrun_dict["current_process_run_state"] = state_dict[
                "{0}".format(current_processrun.state)]
            current_processrun_dict["current_process_task_info"] = current_process_task_info
            current_processrun_dict["current_processrun_dict"] = current_processrun_dict
            current_processrun_dict["start_time_strftime"] = start_time_strftime
            current_processrun_dict["current_delta_time"] = current_delta_time
            current_processrun_dict["current_process_name"] = current_process_name
            current_processrun_dict["current_step_index"] = current_step_index
            current_processrun_dict["all_steps"] = all_steps
            current_processrun_dict["process_rate"] = process_rate
            current_processrun_dict["current_step_name"] = current_step_name
            current_processrun_dict["group_name"] = group_name
            current_processrun_dict["users"] = users
            current_processrun_dict["processrun_url"] = processrun_url
            current_processrun_dict["processrun_id"] = current_processrun.id

            curren_processrun_info_list.append(current_processrun_dict)

    # 系统切换成功率
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))
    process_success_rate_list = []
    if all_processes:
        for process in all_processes:
            process_name = process.name
            all_processrun_list = process.processrun_set.filter(Q(state="DONE") | Q(state="STOP"))
            successful_processruns = process.processrun_set.filter(state="DONE")
            current_process_success_rate = "%.0f" % (len(successful_processruns) / len(
                all_processrun_list) * 100) if all_processrun_list and successful_processruns else 0

            process_dict = {
                "process_name": process_name,
                "current_process_success_rate": current_process_success_rate,
                "color": process.color
            }
            process_success_rate_list.append(process_dict)

    # 右上角消息任务
    return render(request, "index.html",
                  {'username': request.user.userinfo.fullname, "alltask": alltask, "homepage": True,
                   "pagefuns": getpagefuns(funid, request), "success_rate": success_rate,
                   "all_processruns": all_processruns, "last_processrun_time": last_processrun_time,
                   "average_rto": average_rto, "curren_processrun_info_list": curren_processrun_info_list,
                   "process_success_rate_list": process_success_rate_list})


@login_required
def get_process_rto(request):
    # 不同流程最近的12次切换RTO
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))
    process_rto_list = []
    if all_processes:
        for process in all_processes:
            process_name = process.name
            processrun_rto_obj_list = process.processrun_set.filter(state="DONE")
            current_rto_list = []
            for processrun_rto_obj in processrun_rto_obj_list:
                all_step_runs = processrun_rto_obj.steprun_set.exclude(state="9").exclude(
                    step__rto_count_in="0").filter(step__pnode=None)
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
                all_inner_step_runs = processrun_rto_obj.steprun_set.exclude(state="9").filter(
                    step__rto_count_in="0").exclude(
                    step__pnode=None).filter(step__pnode__rto_count_in="1")
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

                current_rto = float("%.2f" % (step_rto / 60))

                current_rto_list.append(current_rto)
            process_dict = {
                "process_name": process_name,
                "current_rto_list": current_rto_list[::-1] if len(current_rto_list) <= 50 else current_rto_list[
                                                                                               -50:][::-1],
                "color": process.color
            }
            process_rto_list.append(process_dict)
    return JsonResponse({"data": process_rto_list})


@login_required
def get_daily_processrun(request):
    all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="STOP")).select_related("process")
    process_success_rate_list = []
    if all_processrun_objs:
        for process_run in all_processrun_objs:
            process_name = process_run.process.name
            start_time = process_run.starttime
            end_time = process_run.endtime
            process_color = process_run.process.color
            process_run_id = process_run.id
            # 进程url
            processrun_url = "/processindex/" + str(process_run.id) + "?s=true"

            process_run_dict = {
                "process_name": process_name,
                "start_time": start_time,
                "end_time": end_time,
                "process_color": process_color,
                "process_run_id": process_run_id,
                "url": processrun_url,
                "invite": "0"
            }
            process_success_rate_list.append(process_run_dict)
    all_walkthrough_invited = Walkthrough.objects.filter(state="PLAN")
    if all_walkthrough_invited:
        for walkthrough_invited in all_walkthrough_invited:
            invitations_dict = {
                "process_name": walkthrough_invited.name,
                "start_time": walkthrough_invited.starttime,
                "end_time": walkthrough_invited.endtime,
                "process_color": "red",
                "process_run_id": walkthrough_invited.id,
                "url": "/walkthrough/",
                "invite": "1",
            }
            process_success_rate_list.append(invitations_dict)
    return JsonResponse({"data": process_success_rate_list})


def login(request):
    auth.logout(request)
    try:
        del request.session['ispuser']
        del request.session['isadmin']
    except KeyError:
        pass
    return render(request, 'login.html')


def userlogin(request):
    if request.method == 'POST':
        result = ""
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            myuserinfo = user.userinfo
            if myuserinfo.forgetpassword:
                myuserinfo.forgetpassword = ""
                myuserinfo.save()
            if request.user.is_authenticated():
                if myuserinfo.state == "0":
                    result = "success1"
                else:
                    result = "success"
                if (request.POST.get('remember', '') != '1'):
                    request.session.set_expiry(0)
                myuser = User.objects.get(username=username)
                usertype = myuser.userinfo.type
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = myuser.is_superuser
            else:
                result = "登录失败，请于客服联系。"
        else:
            result = "用户名或密码不正确。"

    return HttpResponse(result)


def forgetPassword(request):
    if request.method == 'POST':
        result = ""
        email = request.POST.get('email', '')
        alluser = User.objects.filter(email=email)
        if (len(alluser) <= 0):
            result = u"邮箱" + email + u'不存在。'
        else:
            myuserinfo = alluser[0].userinfo
            url = str(uuid.uuid1())
            subject = u'密码重置'
            message = u'用户:' + alluser[0].username + u'您好。' \
                      + u"\n您在云灾备系统申请了密码重置，点击链接进入密码重置页面:" \
                      + u"http://127.0.0.1:8000/resetpassword/" + url
            send_mail(subject, message, settings.EMAIL_HOST_USER, [alluser[0].email])
            myuserinfo.forgetpassword = url
            myuserinfo.save()
            result = "邮件发送成功，请注意查收。"
        return HttpResponse(result)


def resetpassword(request, offset):
    myuserinfo = UserInfo.objects.filter(forgetpassword=offset)
    if len(myuserinfo) > 0:
        myusername = myuserinfo[0].user.username
        return render(request, 'reset.html', {"myusername": myusername})
    else:
        return render(request, 'reset.html', {"error": True})


def reset(request):
    if request.method == 'POST':
        result = ""
        myusername = request.POST.get('username', '')
        password = request.POST.get('password', '')

        alluser = User.objects.filter(username=myusername)
        if (len(alluser) > 0):
            alluser[0].set_password(password)
            alluser[0].save()
            myuserinfo = alluser[0].userinfo
            myuserinfo.forgetpassword = ""
            myuserinfo.save()
            if myuserinfo.state == "0":
                result = "success1"
            else:
                result = "success"
            auth.logout(request)
            user = auth.authenticate(username=myusername, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                usertype = myuserinfo.type
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = alluser[0].is_superuser
        else:
            result = "用户不存在。"
        return HttpResponse(result)


@login_required
def password(request):
    return render(request, 'password.html', {"myusername": request.user.username})


def userpassword(request):
    if request.method == 'POST':
        result = ""
        username = request.POST.get('username', '')
        oldpassword = request.POST.get('oldpassword', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=oldpassword)
        if user is not None and user.is_active:
            alluser = User.objects.filter(username=username)
            if (len(alluser) > 0):
                alluser[0].set_password(password)
                alluser[0].save()
                myuserinfo = alluser[0].userinfo
                myuserinfo.forgetpassword = ""
                myuserinfo.save()
                result = "success"
                auth.logout(request)
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    usertype = myuserinfo.type
                    if usertype == '1':
                        request.session['ispuser'] = True
                    else:
                        request.session['ispuser'] = False
                    request.session['isadmin'] = alluser[0].is_superuser
            else:
                result = "用户异常，修改密码失败。"
        else:
            result = "旧密码输入错误，请重新输入。"

    return HttpResponse(result)


def get_fun_tree(parent, selectid):
    nodes = []
    children = parent.children.order_by("sort").all()
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = child.id
        node["type"] = child.type
        node["data"] = {"url": child.url, "icon": child.icon, "pname": parent.name}
        node["children"] = get_fun_tree(child, selectid)
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def function(request, funid):
    try:
        errors = []
        title = "请选择功能"
        selectid = ""
        id = ""
        pid = ""
        pname = ""
        name = ""
        mytype = ""
        url = ""
        icon = ""
        hiddendiv = "hidden"

        if request.method == 'POST':
            hiddendiv = ""
            id = request.POST.get('id')
            pid = request.POST.get('pid')
            pname = request.POST.get('pname')
            name = request.POST.get('name')
            mytype = request.POST.get('radio2')
            url = request.POST.get('url')
            icon = request.POST.get('icon')
            try:
                id = int(id)

            except:
                raise Http404()
            try:
                pid = int(pid)
            except:
                raise Http404()
            if id == 0:
                selectid = pid
                title = "新建"
            else:

                selectid = id
                title = name

            if name.strip() == '':
                errors.append('功能名称不能为空。')

            else:
                try:
                    pfun = Fun.objects.get(id=pid)
                except:
                    raise Http404()
                try:
                    if id == 0:
                        sort = 1

                        try:
                            maxfun = Fun.objects.filter(pnode=pfun).latest('sort')
                            sort = maxfun.sort + 1
                        except:
                            pass
                        funsave = Fun()
                        funsave.pnode = pfun
                        funsave.name = name
                        funsave.type = mytype
                        funsave.url = url
                        funsave.icon = icon
                        funsave.sort = sort if sort else None
                        funsave.save()
                        title = name
                        id = funsave.id
                        selectid = id
                    else:
                        funsave = Fun.objects.get(id=id)
                        if funsave.type == "node" and mytype == "fun" and len(funsave.children.all()) > 0:
                            errors.append('节点下还有其他节点或功能，无法修改为功能。')
                        else:
                            funsave.name = name
                            funsave.type = mytype
                            funsave.url = url
                            funsave.icon = icon
                            funsave.save()
                            title = name
                except:
                    errors.append('保存失败。')
        treedata = []
        rootnodes = Fun.objects.order_by("sort").filter(pnode=None)
        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.name
                root["id"] = rootnode.id
                root["type"] = "node"
                root["data"] = {"url": rootnode.url, "icon": rootnode.icon, "pname": "无"}
                try:
                    if int(selectid) == rootnode.id:
                        root["state"] = {"opened": True, "selected": True}
                    else:
                        root["state"] = {"opened": True}
                except:
                    root["state"] = {"opened": True}
                root["children"] = get_fun_tree(rootnode, selectid)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return render(request, 'function.html',
                      {'username': request.user.userinfo.fullname, 'errors': errors, "id": id,
                       "pid": pid, "pname": pname, "name": name, "url": url, "icon": icon, "title": title,
                       "mytype": mytype, "hiddendiv": hiddendiv, "treedata": treedata,
                       "pagefuns": getpagefuns(funid, request=request)})
    except:
        return HttpResponseRedirect("/index")


@login_required
def fundel(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        allfun = Fun.objects.filter(id=id)
        if (len(allfun) > 0):
            sort = allfun[0].sort
            pfun = allfun[0].pnode
            allfun[0].delete()
            sortfuns = Fun.objects.filter(pnode=pfun).filter(sort__gt=sort)
            if len(sortfuns) > 0:
                for sortfun in sortfuns:
                    try:
                        sortfun.sort = sortfun.sort - 1
                        sortfun.save()
                    except:
                        pass
            return HttpResponse(1)
        else:
            return HttpResponse(0)


@login_required
def funmove(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        parent = request.POST.get('parent', '')
        old_parent = request.POST.get('old_parent', '')
        position = request.POST.get('position', '')
        old_position = request.POST.get('old_position', '')
        try:
            id = int(id)
        except:
            raise Http404()
        try:
            parent = int(parent)
        except:
            raise Http404()
        try:
            position = int(position)
        except:
            raise Http404()
        try:
            parent = int(parent)
        except:
            raise Http404()
        try:
            old_position = int(old_position)
        except:
            raise Http404()
        oldpfun = Fun.objects.get(id=old_parent)
        oldsort = old_position + 1
        oldfuns = Fun.objects.filter(pnode=oldpfun).filter(sort__gt=oldsort)

        pfun = Fun.objects.get(id=parent)
        sort = position + 1
        funs = Fun.objects.filter(pnode=pfun).filter(sort__gte=sort).exclude(id=id)

        if pfun.type == "fun":
            return HttpResponse("类型")
        else:
            if (len(oldfuns) > 0):
                for oldfun in oldfuns:
                    try:
                        oldfun.sort = oldfun.sort - 1
                        oldfun.save()
                    except:
                        pass

            if (len(funs) > 0):
                for fun in funs:
                    try:
                        fun.sort = fun.sort + 1
                        fun.save()
                    except:
                        pass
            myfun = Fun.objects.get(id=id)
            try:
                myfun.pnode = pfun
                myfun.sort = sort
                myfun.save()
            except:
                pass
            if parent != old_parent:
                return HttpResponse(pfun.name + "^" + str(pfun.id))
            else:
                return HttpResponse("0")


def get_org_tree(parent, selectid, allgroup):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9").all()
    for child in children:
        node = {}
        node["text"] = child.fullname
        node["id"] = child.id
        node["type"] = child.type
        if child.type == "org":
            myallgroup = []
            for group in allgroup:
                myallgroup.append({"groupname": group.name, "id": group.id})
            node["data"] = {"remark": child.remark, "pname": parent.fullname, "myallgroup": myallgroup}
        if child.type == "user":
            noselectgroup = []
            selectgroup = []
            allselectgroup = child.group.all()
            for group in allgroup:
                if group in allselectgroup:
                    selectgroup.append({"groupname": group.name, "id": group.id})
                else:
                    noselectgroup.append({"groupname": group.name, "id": group.id})
            node["data"] = {"pname": parent.fullname, "username": child.user.username, "fullname": child.fullname,
                            "phone": child.phone, "email": child.user.email, "noselectgroup": noselectgroup,
                            "selectgroup": selectgroup}
        node["children"] = get_org_tree(child, selectid, allgroup)
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def organization(request, funid):
    try:
        errors = []
        title = "请选择组织"
        selectid = ""
        id = ""
        pid = ""
        pname = ""
        noselectgroup = []
        selectgroup = []
        username = ""
        fullname = ""
        orgname = ""
        phone = ""
        email = ""
        password = ""
        mytype = ""
        remark = ""
        hiddendiv = "hidden"
        hiddenuser = "hidden"
        hiddenorg = "hidden"
        newpassword = "hidden"
        editpassword = ""
        allgroup = Group.objects.exclude(state="9")
        if request.method == 'POST':
            hiddendiv = ""
            id = request.POST.get('id')
            pid = request.POST.get('pid')
            mytype = request.POST.get('mytype')
            try:
                id = int(id)

            except:
                raise Http404()
            try:
                pid = int(pid)
            except:
                raise Http404()

            if 'usersave' in request.POST:
                hiddenuser = ""
                hiddenorg = "hidden"
                grouplist = request.POST.getlist('source')
                noselectgroup = []
                selectgroup = []
                for group in allgroup:
                    if str(group.id) in grouplist:
                        selectgroup.append({"groupname": group.name, "id": group.id})
                    else:
                        noselectgroup.append({"groupname": group.name, "id": group.id})
                pname = request.POST.get('pname')
                username = request.POST.get('myusername', '')
                fullname = request.POST.get('fullname', '')
                phone = request.POST.get('phone', '')
                email = request.POST.get('email', '')
                password = request.POST.get('password', '')
                if id == 0:
                    newpassword = ""
                    editpassword = "hidden"
                    selectid = pid
                    title = "新建"
                    alluser = User.objects.filter(username=username)
                    if username.strip() == '':
                        errors.append('用户名不能为空。')
                    else:
                        if password.strip() == '':
                            errors.append('密码不能为空。')
                        else:
                            if fullname.strip() == '':
                                errors.append('姓名不能为空。')
                            else:
                                if (len(alluser) > 0):
                                    errors.append('用户名:' + username + '已存在。')
                                else:
                                    try:
                                        newuser = User()
                                        newuser.username = username
                                        newuser.set_password(password)
                                        newuser.email = email
                                        newuser.save()
                                        # 用户扩展信息 profile
                                        profile = UserInfo()  # e*************************
                                        profile.user_id = newuser.id
                                        profile.phone = phone
                                        profile.fullname = fullname
                                        try:
                                            porg = UserInfo.objects.get(id=pid)
                                        except:
                                            raise Http404()
                                        profile.pnode = porg
                                        profile.type = "user"
                                        sort = 1
                                        try:
                                            maxorg = UserInfo.objects.filter(pnode=porg).latest('sort')
                                            sort = maxorg.sort + 1
                                        except:
                                            pass
                                        profile.sort = sort
                                        profile.save()
                                        for group in grouplist:
                                            try:
                                                group = int(group)
                                                mygroup = allgroup.get(id=group)
                                                profile.group.add(mygroup)
                                            except ValueError:
                                                raise Http404()
                                        title = fullname
                                        selectid = profile.id
                                        id = profile.id
                                        newpassword = "hidden"
                                        editpassword = ""
                                    except ValueError:
                                        raise Http404()
                else:
                    selectid = id
                    title = fullname
                    exalluser = User.objects.filter(username=username)
                    if username.strip() == '':
                        errors.append('用户名不能为空。')
                    else:
                        if fullname.strip() == '':
                            errors.append('姓名不能为空。')
                        else:
                            if (len(exalluser) > 0 and exalluser[0].userinfo.id != id):
                                errors.append('用户名:' + username + '已存在。')
                            else:
                                try:
                                    alluserinfo = UserInfo.objects.get(id=id)
                                    alluser = alluserinfo.user
                                    alluser.email = email
                                    alluser.save()
                                    # 用户扩展信息 profile
                                    alluserinfo.phone = phone
                                    alluserinfo.fullname = fullname
                                    alluserinfo.save()
                                    alluserinfo.group.clear()
                                    for group in grouplist:
                                        try:
                                            group = int(group)
                                            mygroup = allgroup.get(id=group)
                                            alluserinfo.group.add(mygroup)
                                        except ValueError:
                                            raise Http404()
                                    title = fullname
                                except:
                                    errors.append('保存失败。')

            else:
                if 'orgsave' in request.POST:
                    hiddenuser = "hidden"
                    hiddenorg = ""
                    pname = request.POST.get('orgpname')
                    orgname = request.POST.get('orgname', '')
                    remark = request.POST.get('remark', '')
                    if id == 0:
                        selectid = pid
                        title = "新建"
                        try:
                            porg = UserInfo.objects.get(id=pid)
                        except:
                            raise Http404()
                        allorg = UserInfo.objects.filter(fullname=orgname, pnode=porg)
                        if orgname.strip() == '':
                            errors.append('组织名称不能为空。')
                        else:
                            if (len(allorg) > 0):
                                errors.append(orgname + '已存在。')
                            else:
                                try:
                                    profile = UserInfo()  # e*************************
                                    profile.fullname = orgname
                                    profile.pnode = porg
                                    profile.remark = remark
                                    profile.type = "org"
                                    sort = 1
                                    try:
                                        maxorg = UserInfo.objects.filter(pnode=porg).latest('sort')
                                        sort = maxorg.sort + 1
                                    except:
                                        pass
                                    profile.sort = sort
                                    profile.save()
                                    title = orgname
                                    selectid = profile.id
                                    id = profile.id
                                except ValueError:
                                    raise Http404()
                    else:
                        selectid = id
                        title = orgname
                        try:
                            porg = UserInfo.objects.get(id=pid)
                        except:
                            raise Http404()
                        exalluser = UserInfo.objects.filter(fullname=orgname, pnode=porg).exclude(state="9")
                        if orgname.strip() == '':
                            errors.append('组织名称不能为空。')
                        else:
                            if (len(exalluser) > 0 and exalluser[0].id != id):
                                errors.append(username + '已存在。')
                            else:
                                try:
                                    alluserinfo = UserInfo.objects.get(id=id)
                                    alluserinfo.fullname = orgname
                                    alluserinfo.remark = remark
                                    alluserinfo.save()
                                    title = orgname
                                except:
                                    errors.append('保存失败。')

        treedata = []
        rootnodes = UserInfo.objects.order_by("sort").exclude(state="9").filter(pnode=None, type="org")
        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.fullname
                root["id"] = rootnode.id
                root["type"] = "org"
                myallgroup = []
                for group in allgroup:
                    myallgroup.append({"groupname": group.name, "id": group.id})
                root["data"] = {"remark": rootnode.remark, "pname": "无", "myallgroup": myallgroup}
                try:
                    if int(selectid) == rootnode.id:
                        root["state"] = {"opened": True, "selected": True}
                    else:
                        root["state"] = {"opened": True}
                except:
                    root["state"] = {"opened": True}
                root["children"] = get_org_tree(rootnode, selectid, allgroup)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return render(request, 'organization.html',
                      {'username': request.user.userinfo.fullname, 'errors': errors, "id": id, "orgname": orgname,
                       "pid": pid, "pname": pname, "fullname": fullname, "phone": phone, "myusername": username,
                       "email": email, "password": password, "noselectgroup": noselectgroup,
                       "selectgroup": selectgroup, "remark": remark, "title": title, "mytype": mytype,
                       "hiddenuser": hiddenuser, "hiddenorg": hiddenorg, "newpassword": newpassword,
                       "editpassword": editpassword, "hiddendiv": hiddendiv, "treedata": treedata,
                       "pagefuns": getpagefuns(funid, request=request)})

    except:
        return HttpResponseRedirect("/index")


@login_required
def orgdel(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        userinfo = UserInfo.objects.get(id=id)
        sort = userinfo.sort
        userinfo.state = "9"
        userinfo.sort = 9999
        userinfo.save()

        if userinfo.type == "user":
            user = userinfo.user
            user.is_active = 0
            user.save()

        userinfos = UserInfo.objects.filter(pnode=userinfo.pnode).filter(sort__gt=sort).exclude(state="9")
        if (len(userinfos) > 0):
            for myuserinfo in userinfos:
                try:
                    myuserinfo.sort = myuserinfo.sort - 1
                    myuserinfo.save()
                except:
                    pass

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def orgmove(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        parent = request.POST.get('parent', '')
        old_parent = request.POST.get('old_parent', '')
        position = request.POST.get('position', '')
        old_position = request.POST.get('old_position', '')
        try:
            id = int(id)
        except:
            raise Http404()
        try:
            parent = int(parent)
        except:
            raise Http404()
        try:
            position = int(position)
        except:
            raise Http404()
        try:
            parent = int(parent)
        except:
            raise Http404()
        try:
            old_position = int(old_position)
        except:
            raise Http404()
        oldpuserinfo = UserInfo.objects.get(id=old_parent)
        oldsort = old_position + 1
        olduserinfos = UserInfo.objects.filter(pnode=oldpuserinfo).filter(sort__gt=oldsort)

        puserinfo = UserInfo.objects.get(id=parent)
        sort = position + 1
        userinfos = UserInfo.objects.filter(pnode=puserinfo).filter(sort__gte=sort).exclude(id=id).exclude(
            state="9")

        myuserinfo = UserInfo.objects.get(id=id)
        if puserinfo.type == "user":
            return HttpResponse("类型")
        else:
            usersame = UserInfo.objects.filter(pnode=puserinfo).filter(fullname=myuserinfo.fullname).exclude(
                id=id).exclude(state="9")
            if (len(usersame) > 0):
                return HttpResponse("重名")
            else:
                if (len(olduserinfos) > 0):
                    for olduserinfo in olduserinfos:
                        try:
                            olduserinfo.sort = olduserinfo.sort - 1
                            olduserinfo.save()
                        except:
                            pass
                if (len(userinfos) > 0):
                    for userinfo in userinfos:
                        try:
                            userinfo.sort = userinfo.sort + 1
                            userinfo.save()
                        except:
                            pass

                try:
                    myuserinfo.pnode = puserinfo
                    myuserinfo.sort = sort
                    myuserinfo.save()
                except:
                    pass
                if parent != old_parent:
                    return HttpResponse(puserinfo.fullname + "^" + str(puserinfo.id))
                else:
                    return HttpResponse("0")


@login_required
def orgpassword(request):
    if 'id' in request.POST:
        id = request.POST.get('id')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        try:
            offset = int(id)
            userinfo = UserInfo.objects.get(id=id)
            user = userinfo.user
            user.set_password(password1)
            user.save()
            return HttpResponse("1")
        except:
            HttpResponse('修改密码失败，请于管理员联系。')


@login_required
def group(request, funid):
    try:
        allgroup = Group.objects.all().exclude(state="9")

        return render(request, 'group.html',
                      {'username': request.user.userinfo.fullname,
                       "allgroup": allgroup, "pagefuns": getpagefuns(funid, request)})
    except:
        return HttpResponseRedirect("/index")


@login_required
def groupsave(request):
    if 'id' in request.POST:
        result = {}
        id = request.POST.get('id', '')
        name = request.POST.get('name', '')
        remark = request.POST.get('remark', '')
        try:
            id = int(id)
        except:
            raise Http404()
        if name.strip() == '':
            result["res"] = '角色名称不能为空。'
        else:
            if id == 0:
                allgroup = Group.objects.filter(name=name).exclude(state="9")
                if (len(allgroup) > 0):
                    result["res"] = name + '已存在。'
                else:
                    groupsave = Group()
                    groupsave.name = name
                    groupsave.remark = remark
                    groupsave.save()
                    result["res"] = "新增成功。"
                    result["data"] = groupsave.id
            else:
                allgroup = Group.objects.filter(name=name).exclude(id=id).exclude(state="9")
                if (len(allgroup) > 0):
                    result["res"] = name + '已存在。'
                else:
                    try:
                        groupsave = Group.objects.get(id=id)
                        groupsave.name = name
                        groupsave.remark = remark
                        groupsave.save()
                        result["res"] = "修改成功。"
                    except:
                        result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


@login_required
def groupdel(request):
    if 'id' in request.POST:
        result = ""
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        allgroup = Group.objects.filter(id=id)
        result = '角色不存在。'
        if (len(allgroup) > 0):
            groupsave = allgroup[0]
            groupsave.state = "9"
            groupsave.save()
            result = "删除成功。"
        else:
            result = '角色不存在。'
        return HttpResponse(result)


def group_get_user_tree(parent, selectusers):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9").all()
    for child in children:
        node = {}
        node["text"] = child.fullname
        node["id"] = "user_" + str(child.id)
        node["type"] = child.type
        if child.type == "user" and child in selectusers:
            node["state"] = {"selected": True}
        node["children"] = group_get_user_tree(child, selectusers)
        nodes.append(node)
    return nodes


@login_required
def getusertree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()

        treedata = []
        groupsave = Group.objects.get(id=id)
        selectusers = groupsave.userinfo_set.all()

        rootnodes = UserInfo.objects.order_by("sort").exclude(state="9").filter(pnode=None, type="org")

        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.fullname
                root["id"] = "user_" + str(rootnode.id)
                root["type"] = "org"
                root["state"] = {"opened": True}
                root["children"] = group_get_user_tree(rootnode, selectusers)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return HttpResponse(treedata)


@login_required
def groupsaveusertree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        selectedusers = request.POST.get('selecteduser', '')
        selectedusers = selectedusers.split(',')

        try:
            id = int(id)
        except:
            raise Http404()
        groupsave = Group.objects.get(id=id)
        groupsave.userinfo_set.clear()
        if len(selectedusers) > 0:
            for selecteduser in selectedusers:
                try:
                    myuser = UserInfo.objects.get(id=int(selecteduser.replace("user_", "")))
                    if myuser.type == "user":
                        myuser.group.add(groupsave)
                except:
                    pass
        return HttpResponse("保存成功。")


def group_get_fun_tree(parent, selectfuns):
    nodes = []
    children = parent.children.order_by("sort").all()
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = "fun_" + str(child.id)
        node["type"] = child.type
        if child.type == "fun" and child in selectfuns:
            node["state"] = {"selected": True}
        node["children"] = group_get_fun_tree(child, selectfuns)
        nodes.append(node)
    return nodes


@login_required
def getfuntree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()

        treedata = []
        groupsave = Group.objects.get(id=id)
        selectfuns = groupsave.fun.all()

        rootnodes = Fun.objects.order_by("sort").filter(pnode=None, type="node")

        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.name
                root["id"] = "fun_" + str(rootnode.id)
                root["type"] = "node"
                root["state"] = {"opened": True}
                root["children"] = group_get_fun_tree(rootnode, selectfuns)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return HttpResponse(treedata)


@login_required
def groupsavefuntree(request):
    id = request.POST.get('id', '')
    selectedfuns = request.POST.get('selectedfun', '')
    selectedfuns = selectedfuns.split(',')

    try:
        id = int(id)
    except:
        raise Http404()
    groupsave = Group.objects.get(id=id)
    groupsave.fun.clear()
    if len(selectedfuns) > 0:
        for selectedfun in selectedfuns:
            try:
                myfun = Fun.objects.get(id=int(selectedfun.replace("fun_", "")))
                if myfun.type == "fun":
                    groupsave.fun.add(myfun)
            except:
                pass
    return HttpResponse("保存成功。")


def get_script_tree(parent, select_id):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9")
    for child in children:
        node = dict()
        node["text"] = child.name
        node["id"] = child.id
        node["type"] = child.type
        if child.type == "NODE":  # 节点
            node["data"] = {
                "remark": child.remark,
                "pname": parent.name
            }
        if child.type == "INTERFACE":  # 接口
            node["data"] = {
                "pname": parent.name,
                "remark": child.remark,
                "code": child.code,
                "name": child.name,
                "type": child.type,
                "interface_type": child.interface_type,
                "origin": child.origin.id if child.origin else "",
                "commv_interface": child.commv_interface,
                "ip": child.hosts_manage.id if child.hosts_manage else "",
                "script_text": child.script_text,
                "success_text": child.succeedtext,
                "log_address": child.log_address,
            }
        node["children"] = get_script_tree(child, select_id)
        try:
            if int(select_id) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def script(request, funid):
    errors = []
    select_id = ""  # 当前修改的节点
    # 接口信息与节点信息隐藏设置
    interface_hidden = "hidden"
    node_hidden = "hidden"
    right_info_hidden = "hidden"

    if request.method == 'POST':
        id = request.POST.get('id', '')
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        host_id = request.POST.get('ip', '')

        # script_text
        script_text = request.POST.get('script_text', '')

        success_text = request.POST.get('success_text', '')
        log_address = request.POST.get('log_address', '')

        # commvault接口
        interface_type = request.POST.get('interface_type', '')
        origin = request.POST.get('origin', '')
        commv_interface = request.POST.get('commv_interface', '')

        pid = request.POST.get('pid', '')
        my_type = request.POST.get('my_type', '')
        remark = request.POST.get('remark', '')

        # 节点
        node_remark = request.POST.get('node_remark', '')
        node_name = request.POST.get('node_name', '')

        # 节点存储方法
        def node_save(save_data):
            result = {}
            # 删除ID
            copy_save_data = copy.deepcopy(save_data)
            copy_save_data.pop("id")
            if save_data["id"] == 0:
                # 排序
                sort = 1
                try:
                    max_sort = Script.objects.exclude(state="9").filter(pnode_id=save_data["pnode_id"]).aggregate(
                        max_sort=Max('sort', distinct=True))["max_sort"]
                    sort = max_sort + 1
                except:
                    pass
                copy_save_data["sort"] = sort
                try:
                    scriptsave = Script.objects.create(**copy_save_data)
                    result["res"] = "新增成功。"
                    result["data"] = scriptsave.id
                except Exception as e:
                    print(e)
                    result["res"] = "新增失败。"
            else:
                # 修改
                try:
                    Script.objects.filter(id=save_data["id"]).update(**copy_save_data)
                    result["res"] = "修改成功。"
                    result["data"] = save_data["id"]
                except:
                    result["res"] = "修改失败。"

        # 接口存储方法
        def interface_save(save_data, cur_host_manage=None):
            result = {}

            if save_data["id"] == 0:
                allscript = Script.objects.filter(code=save_data["code"]).exclude(state="9").filter(step_id=None)
                if allscript.exists():
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    scriptsave = Script()
                    scriptsave.code = save_data["code"]
                    scriptsave.name = save_data["name"]
                    scriptsave.type = save_data["type"]
                    scriptsave.pnode_id = save_data["pnode_id"]
                    scriptsave.remark = save_data["remark"]

                    # 判断是否commvault/脚本
                    if save_data["interface_type"] == "Commvault":
                        scriptsave.hosts_manage_id = None
                        scriptsave.script_text = ""
                        scriptsave.succeedtext = ""
                        scriptsave.log_address = ""

                        scriptsave.origin_id = save_data["origin"]
                        scriptsave.commv_interface = save_data["commv_interface"]
                    else:
                        scriptsave.hosts_manage_id = cur_host_manage.id
                        scriptsave.script_text = save_data["script_text"]
                        scriptsave.succeedtext = save_data["succeedtext"]
                        scriptsave.log_address = save_data["log_address"]

                        scriptsave.origin_id = None
                        scriptsave.commv_interface = ""

                    scriptsave.interface_type = save_data["interface_type"]

                    # 排序
                    sort = 1
                    try:
                        max_sort = Script.objects.exclude(state="9").filter(pnode_id=save_data["pnode_id"]).aggregate(
                            max_sort=Max('sort', distinct=True))["max_sort"]
                        sort = max_sort + 1
                    except:
                        pass
                    scriptsave.sort = sort

                    scriptsave.save()
                    result["res"] = "新增成功。"
                    result["data"] = scriptsave.id
            else:
                # 修改
                allscript = Script.objects.filter(code=save_data["code"]).exclude(id=save_data["id"]).exclude(
                    state="9").filter(step_id=None)
                if allscript.exists():
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    try:
                        scriptsave = Script.objects.get(id=save_data["id"])
                        scriptsave.code = save_data["code"]
                        scriptsave.name = save_data["name"]
                        scriptsave.type = save_data["type"]
                        scriptsave.remark = save_data["remark"]

                        # 判断是否commvault/脚本
                        if save_data["interface_type"] == "commvault":
                            scriptsave.hosts_manage_id = None
                            scriptsave.script_text = ""
                            scriptsave.succeedtext = ""
                            scriptsave.log_address = ""

                            scriptsave.origin_id = save_data["origin"]
                            scriptsave.commv_interface = save_data["commv_interface"]
                        else:
                            scriptsave.hosts_manage_id = cur_host_manage.id
                            scriptsave.script_text = save_data["script_text"]
                            scriptsave.succeedtext = save_data["succeedtext"]
                            scriptsave.log_address = save_data["log_address"]

                            scriptsave.origin_id = None
                            scriptsave.commv_interface = ""

                        scriptsave.interface_type = save_data["interface_type"]

                        scriptsave.save()
                        result["res"] = "修改成功。"
                        result["data"] = scriptsave.id
                    except Exception as e:
                        print("scriptsave edit error:%s" % e)
                        result["res"] = "修改失败。"

            return result

        try:
            id = int(id)
            pid = int(pid)
        except ValueError as e:
            errors.append('网络连接异常。')
        else:
            # NODE/INTERFACE
            if my_type == "NODE":
                save_data = {
                    "id": id,
                    "code": "",
                    "name": node_name,
                    "script_text": "",
                    "succeedtext": "",
                    "log_address": "",
                    "hosts_manage_id": None,
                    "interface_type": "",
                    "origin": None,
                    "commv_interface": "",
                    "remark": node_remark,
                    "pnode_id": pid,
                    "type": my_type,
                }
                result = node_save(save_data)
            else:
                save_data = {
                    "id": id,
                    "code": code,
                    "name": name,
                    "script_text": script_text,
                    "succeedtext": success_text,
                    "log_address": log_address,
                    "hosts_manage_id": host_id,
                    "interface_type": interface_type,
                    "origin": origin,
                    "commv_interface": commv_interface,
                    "remark": remark,
                    "pnode_id": pid,
                    "type": my_type,
                }
                if code.strip() == '':
                    errors.append('接口编码不能为空。')
                else:
                    if name.strip() == '':
                        errors.append('接口名称不能为空。')
                    else:
                        # 区分interface_type: commvault/脚本
                        if interface_type.strip() == "":
                            errors.append('接口类型未选择。')
                        else:
                            if interface_type == "Commvault":
                                if origin.strip() == "":
                                    errors.append('commvault源端未选择。')
                                else:
                                    if commv_interface.strip() == "":
                                        errors.append('commvault接口未选择。')
                                    else:
                                        result = interface_save(save_data, cur_host_manage=None)
                            else:
                                try:
                                    host_id = int(host_id)
                                except ValueError as e:
                                    print("host_id:%s" % e)
                                    errors.append('网络连接异常。')
                                else:
                                    if not host_id:
                                        errors.append('脚本存放的主机未选择。')
                                    else:
                                        if script_text.strip() == '':
                                            errors.append('脚本内容不能为空。')
                                        else:
                                            try:
                                                cur_host_manage = HostsManage.objects.get(id=host_id)
                                            except HostsManage.DoesNotExist as e:
                                                print(e)
                                                errors.append('所选主机不存在。')
                                            else:
                                                result = interface_save(save_data, cur_host_manage=cur_host_manage)

    tree_data = []
    root_nodes = Script.objects.order_by("sort").exclude(state="9").filter(pnode=None, type="NODE")

    for root_node in root_nodes:
        root = dict()
        root["text"] = root_node.name
        root["id"] = root_node.id
        root["type"] = "NODE"
        root["data"] = {
            "remark": root_node.remark,
            "pname": "无"
        }

        root["children"] = get_script_tree(root_node, select_id)
        tree_data.append(root)
    tree_data = json.dumps(tree_data, ensure_ascii=False)
    # 主机选项
    all_hosts_manage = HostsManage.objects.exclude(state="9")

    # commvault源端客户端
    all_origins = Origin.objects.exclude(state="9").order_by("utils__name")

    return render(request, 'script.html', {
        'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
        "errors": errors, "all_hosts_manage": all_hosts_manage, "all_origins": all_origins,
        "tree_data": tree_data, "interface_hidden": interface_hidden, "node_hidden": node_hidden,
        "right_info_hidden": right_info_hidden
    })


@login_required
def scriptdata(request):
    result = []
    allscript = Script.objects.exclude(state="9").filter(step_id=None).select_related("origin", "hosts_manage")
    if (len(allscript) > 0):
        for script in allscript:
            # modify
            if script.interface_type == "commvault":
                cur_origin = script.origin
                if cur_origin:
                    result.append({
                        "id": script.id,
                        "code": script.code,
                        "name": script.name,
                        "ip": "",
                        "host_id": "",
                        "script_text": "",
                        "success_text": "",
                        "log_address": "",

                        "interface_type": script.interface_type,
                        "commv_interface": script.commv_interface,
                        "origin": cur_origin.id
                    })
            else:
                cur_host = script.hosts_manage
                if cur_host:
                    host_id = cur_host.id
                    ip = cur_host.host_ip

                    result.append({
                        "id": script.id,
                        "code": script.code,
                        "name": script.name,
                        "ip": ip,
                        "host_id": host_id,
                        "script_text": script.script_text,
                        "success_text": script.succeedtext,
                        "log_address": script.log_address,

                        "interface_type": script.interface_type,
                        "commv_interface": "",
                        "origin": "",
                    })

    return HttpResponse(json.dumps({"data": result}))


@login_required
def scriptdel(request):
    """
    当删除脚本管理中的脚本的同时，需要删除预案中绑定的脚本；
    :param request:
    :return:
    """
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        script = Script.objects.get(id=id)
        script.state = "9"
        script.save()

        script_code = script.code
        related_scripts = Script.objects.filter(code=script_code)
        for related_script in related_scripts:
            related_script.state = "9"
            related_script.save()

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def scriptsave(request):
    if 'id' in request.POST:
        result = {}
        id = request.POST.get('id', '')
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        host_id = request.POST.get('ip', '')

        # script_text
        script_text = request.POST.get('script_text', '')

        success_text = request.POST.get('success_text', '')
        log_address = request.POST.get('log_address', '')

        # commvault接口
        interface_type = request.POST.get('interface_type', '')
        origin = request.POST.get('origin', '')
        commv_interface = request.POST.get('commv_interface', '')

        # 定义存储的方法
        def script_save(save_data, cur_host_manage=None):
            result = {}

            if save_data["id"] == 0:
                allscript = Script.objects.filter(code=save_data["code"]).exclude(state="9").filter(step_id=None)
                if allscript.exists():
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    scriptsave = Script()
                    scriptsave.code = save_data["code"]
                    scriptsave.name = save_data["name"]

                    # 判断是否commvault/脚本
                    if save_data["interface_type"] == "commvault":
                        scriptsave.hosts_manage_id = None
                        scriptsave.script_text = ""
                        scriptsave.succeedtext = ""
                        scriptsave.log_address = ""

                        scriptsave.origin_id = save_data["origin"]
                        scriptsave.commv_interface = save_data["commv_interface"]
                    else:
                        scriptsave.hosts_manage_id = cur_host_manage.id
                        scriptsave.script_text = save_data["script_text"]
                        scriptsave.succeedtext = save_data["success_text"]
                        scriptsave.log_address = save_data["log_address"]

                        scriptsave.origin_id = None
                        scriptsave.commv_interface = ""

                    scriptsave.interface_type = save_data["interface_type"]
                    scriptsave.save()
                    result["res"] = "新增成功。"
                    result["data"] = scriptsave.id
            else:
                # 修改
                allscript = Script.objects.filter(code=save_data["code"]).exclude(id=save_data["id"]).exclude(
                    state="9").filter(step_id=None)
                if allscript.exists():
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    try:
                        scriptsave = Script.objects.get(id=save_data["id"])
                        scriptsave.code = save_data["code"]
                        scriptsave.name = save_data["name"]

                        # 判断是否commvault/脚本
                        if save_data["interface_type"] == "commvault":
                            scriptsave.hosts_manage_id = None
                            scriptsave.script_text = ""
                            scriptsave.succeedtext = ""
                            scriptsave.log_address = ""

                            scriptsave.origin_id = save_data["origin"]
                            scriptsave.commv_interface = save_data["commv_interface"]
                        else:
                            scriptsave.hosts_manage_id = cur_host_manage.id
                            scriptsave.script_text = save_data["script_text"]
                            scriptsave.succeedtext = save_data["success_text"]
                            scriptsave.log_address = save_data["log_address"]

                            scriptsave.origin_id = None
                            scriptsave.commv_interface = ""

                        scriptsave.interface_type = save_data["interface_type"]
                        scriptsave.save()
                        result["res"] = "修改成功。"
                        result["data"] = scriptsave.id
                    except Exception as e:
                        print("scriptsave edit error:%s" % e)
                        result["res"] = "修改失败。"
            return result

        try:
            id = int(id)
        except ValueError as e:
            print("id:%s" % e)
            result["res"] = '网络连接异常。'
        else:
            if code.strip() == '':
                result["res"] = '接口编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '接口名称不能为空。'
                else:
                    # 区分interface_type: commvault/脚本
                    if interface_type.strip() == "":
                        result["res"] = '接口类型未选择。'
                    else:
                        save_data = {
                            "id": id,
                            "code": code,
                            "name": name,
                            "script_text": script_text,
                            "success_text": success_text,
                            "log_address": log_address,
                            "host_id": host_id,
                            "interface_type": interface_type,
                            "origin": origin,
                            "commv_interface": commv_interface
                        }

                        if interface_type == "commvault":
                            if origin.strip() == "":
                                result["res"] = 'commvault源端未选择。'
                            else:
                                if commv_interface.strip() == "":
                                    result["res"] = 'commvault接口未选择。'
                                else:
                                    result = script_save(save_data, cur_host_manage=None)
                        else:
                            try:
                                host_id = int(host_id)
                            except ValueError as e:
                                print("host_id:%s" % e)
                                result["res"] = '网络连接异常。'
                            else:
                                if not host_id:
                                    result["res"] = '脚本存放的主机未选择。'
                                else:
                                    if script_text.strip() == '':
                                        result["res"] = '脚本内容不能为空。'
                                    else:
                                        try:
                                            cur_host_manage = HostsManage.objects.get(id=host_id)
                                        except HostsManage.DoesNotExist as e:
                                            print(e)
                                            result["res"] = '所选主机不存在。'
                                        else:
                                            result = script_save(save_data, cur_host_manage=cur_host_manage)

        return HttpResponse(json.dumps(result))


@login_required
def processscriptsave(request):
    if 'id' in request.POST:
        result = {}
        processid = request.POST.get('processid', '')
        pid = request.POST.get('pid', '')
        id = request.POST.get('id', '')
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        script_text = request.POST.get('script_text', '')

        success_text = request.POST.get('success_text', '')
        log_address = request.POST.get('log_address', '')
        host_id = request.POST.get('host_id', '')

        # commvault接口
        interface_type = request.POST.get('interface_type', '')
        origin = request.POST.get('origin', '')
        commv_interface = request.POST.get('commv_interface', '')

        script_sort = request.POST.get('script_sort', '')

        # 定义存储的方法
        def process_script_save(save_data, cur_host_manage=None):
            result = {}

            if save_data["id"] == 0:
                allscript = Script.objects.filter(code=save_data["code"]).exclude(state="9").filter(
                    step_id=save_data["pid"])
                if (len(allscript) > 0):
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    steplist = Step.objects.filter(process_id=save_data["processid"])
                    if len(steplist) > 0:
                        scriptsave = Script()
                        scriptsave.code = save_data["code"]
                        scriptsave.name = save_data["name"]
                        scriptsave.sort = save_data["script_sort"]

                        # 判断是否commvault/脚本
                        if save_data["interface_type"] == "commvault":
                            scriptsave.hosts_manage_id = None
                            scriptsave.script_text = ""
                            scriptsave.succeedtext = ""
                            scriptsave.log_address = ""

                            scriptsave.origin_id = save_data["origin"]
                            scriptsave.commv_interface = save_data["commv_interface"]
                        else:
                            scriptsave.hosts_manage_id = cur_host_manage.id
                            scriptsave.script_text = save_data["script_text"]
                            scriptsave.succeedtext = save_data["success_text"]
                            scriptsave.log_address = save_data["log_address"]

                            scriptsave.origin_id = None
                            scriptsave.commv_interface = ""

                        scriptsave.step_id = save_data["pid"]
                        scriptsave.interface_type = save_data["interface_type"]
                        scriptsave.save()
                        result["res"] = "新增成功。"

                        ############################################################
                        # result["data"] = [{"script_id": 1, "script_name": "2"}]  #
                        # 当前脚本所在步骤的所有脚本按排序构造数组                   #
                        ############################################################
                        script_info_list = []
                        cur_step = scriptsave.step
                        all_scripts = cur_step.script_set.exclude(state="9").order_by("sort")
                        for script in all_scripts:
                            script_info_list.append({
                                "script_id": script.id,
                                "script_name": script.name
                            })
                        result["data"] = script_info_list
            else:
                # 修改
                allscript = Script.objects.filter(code=save_data["code"]).exclude(id=save_data["id"]).exclude(
                    state="9").filter(step_id=save_data["pid"])
                if (len(allscript) > 0):
                    result["res"] = '脚本编码:' + save_data["code"] + '已存在。'
                else:
                    try:
                        scriptsave = Script.objects.get(id=save_data["id"])

                        scriptsave.code = save_data["code"]
                        scriptsave.name = save_data["name"]
                        scriptsave.sort = save_data["script_sort"]

                        # 判断是否commvault/脚本
                        if save_data["interface_type"] == "commvault":
                            scriptsave.hosts_manage_id = None
                            scriptsave.script_text = ""
                            scriptsave.succeedtext = ""
                            scriptsave.log_address = ""

                            scriptsave.origin_id = save_data["origin"]
                            scriptsave.commv_interface = save_data["commv_interface"]
                        else:
                            scriptsave.hosts_manage_id = cur_host_manage.id
                            scriptsave.script_text = save_data["script_text"]
                            scriptsave.succeedtext = save_data["success_text"]
                            scriptsave.log_address = save_data["log_address"]

                            scriptsave.origin_id = None
                            scriptsave.commv_interface = ""

                        scriptsave.interface_type = save_data["interface_type"]
                        scriptsave.save()
                        result["res"] = "修改成功。"

                        ############################################################
                        # result["data"] = [{"script_id": 1, "script_name": "2"}]  #
                        # 当前脚本所在步骤的所有脚本按排序构造数组                   #
                        ############################################################
                        script_info_list = []
                        cur_step = scriptsave.step
                        all_scripts = cur_step.script_set.exclude(state="9").order_by("sort")
                        for script in all_scripts:
                            script_info_list.append({
                                "script_id": script.id,
                                "script_name": script.name
                            })
                        result["data"] = script_info_list
                    except Exception as e:
                        print("scriptsave edit error:%s" % e)
                        result["res"] = "修改失败。"
            return result

        try:
            id = int(id)
            pid = int(pid)
            processid = int(processid)
        except ValueError as e:
            print("id, pid, processid:%s" % e)
            result["res"] = '网络连接异常。'
        else:
            if code.strip() == '':
                result["res"] = '接口编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '接口名称不能为空。'
                else:
                    try:
                        script_sort = int(script_sort)
                    except ValueError as e:
                        result["res"] = '脚本排序不能为空。'
                    else:
                        # 区分interface_type: commvault/脚本
                        if interface_type.strip() == "":
                            result["res"] = '接口类型未选择。'
                        else:
                            save_data = {
                                "processid": processid,
                                "pid": pid,
                                "id": id,
                                "code": code,
                                "name": name,
                                "script_text": script_text,
                                "success_text": success_text,
                                "log_address": log_address,
                                "host_id": host_id,
                                "interface_type": interface_type,
                                "origin": origin,
                                "commv_interface": commv_interface,
                                "script_sort": script_sort
                            }

                            if interface_type == "commvault":
                                if origin.strip() == "":
                                    result["res"] = 'commvault源端未选择。'
                                else:
                                    if commv_interface.strip() == "":
                                        result["res"] = 'commvault接口未选择。'
                                    else:
                                        result = process_script_save(save_data, cur_host_manage=None)
                            else:
                                try:
                                    host_id = int(host_id)
                                except ValueError as e:
                                    print("host_id:%s" % e)
                                    result["res"] = '网络连接异常。'
                                else:
                                    if not host_id:
                                        result["res"] = '脚本存放的主机未选择。'
                                    else:
                                        if script_text.strip() == '':
                                            result["res"] = '脚本内容不能为空。'
                                        else:
                                            try:
                                                cur_host_manage = HostsManage.objects.get(id=host_id)
                                            except HostsManage.DoesNotExist as e:
                                                print(e)
                                                result["res"] = '所选主机不存在。'
                                            else:
                                                result = process_script_save(save_data,
                                                                             cur_host_manage=cur_host_manage)

        return HttpResponse(json.dumps(result))


@login_required
def verify_items_save(request):
    if 'id' in request.POST:
        result = {}
        id = request.POST.get('id', '')
        name = request.POST.get('name', '')
        process_id = request.POST.get('processid', '')
        step_id = request.POST.get('step_id', '')
        try:
            id = int(id)
        except:
            raise Http404()

        if name.strip() == '':
            result["res"] = '名称不能为空。'
        else:
            if id == 0:
                verify_save = VerifyItems()
                verify_save.name = name
                verify_save.step_id = step_id if step_id else None
                verify_save.save()
                result["res"] = "新增成功。"
                result["data"] = verify_save.id
            else:
                try:
                    verify_save = VerifyItems.objects.get(id=id)
                    verify_save.name = name
                    verify_save.save()
                    result["res"] = "修改成功。"
                    result["data"] = verify_save.id
                except:
                    result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


@login_required
def get_verify_items_data(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        verify_id = request.POST.get("verify_id", "")
        all_verify_items = VerifyItems.objects.exclude(state="9").filter(id=verify_id)
        verify_data = ""
        if (len(all_verify_items) > 0):
            verify_data = {"id": all_verify_items[0].id, "name": all_verify_items[0].name}
        return HttpResponse(json.dumps(verify_data))


@login_required
def remove_verify_item(request):
    # 移除当前步骤中的脚本关联
    verify_id = request.POST.get("verify_id", "")
    try:
        current_verify_item = VerifyItems.objects.filter(id=verify_id)[0]
    except:
        pass
    else:
        current_verify_item.state = "9"
        current_verify_item.save()
    return JsonResponse({
        "status": 1
    })


@login_required
def get_script_data(request):
    status = 1
    info = '获取脚本信息成功。'

    id = request.POST.get('id', '')
    try:
        id = int(id)
    except:
        status = 0
        info = '步骤未创建，请先保存步骤后添加脚本。'
    script_id = request.POST.get("script_id", "")
    allscript = Script.objects.exclude(state="9").filter(id=script_id).select_related("origin")
    script_data = {}
    if allscript.exists():
        cur_script = allscript[0]
        print(cur_script.hosts_manage_id)
        cur_host_manage = cur_script.hosts_manage
        script_data = {
            "id": cur_script.id,
            "code": cur_script.code,
            "name": cur_script.name,
            "host_id": cur_host_manage.id if cur_host_manage else "",
            "script_text": cur_script.script_text,
            "success_text": cur_script.succeedtext,
            "log_address": cur_script.log_address,
            # commvault
            "interface_type": cur_script.interface_type,
            "origin": cur_script.origin.id if cur_script.origin else "",
            "commv_interface": cur_script.commv_interface,

            "script_sort": cur_script.sort
        }
    else:
        status = 0
        info = '当前脚本不存在。'
    return JsonResponse({
        'status': status,
        'info': info,
        'data': script_data,
    })


@login_required
def remove_script(request):
    # 移除当前步骤中的脚本关联
    script_id = request.POST.get("script_id", "")
    try:
        current_script = Script.objects.filter(id=script_id)[0]
    except:
        pass
    else:
        # current_script.delete()
        current_script.state = "9"
        current_script.save()
    return JsonResponse({
        "status": 1
    })


@login_required
def setpsave(request):
    if request.method == 'POST':
        result = ""
        id = request.POST.get('id', '')
        pid = request.POST.get('pid', '')
        name = request.POST.get('name', '')
        time = request.POST.get('time', '')
        skip = request.POST.get('skip', '')
        approval = request.POST.get('approval', '')
        group = request.POST.get('group', '')
        rto_count_in = request.POST.get('rto_count_in', '')
        remark = request.POST.get('remark', '')
        force_exec = request.POST.get('force_exec', '')
        process_id = request.POST.get('process_id', '')
        data = ""
        try:
            id = int(id)
        except:
            return JsonResponse({
                "result": "网络异常。",
                "data": data
            })

        try:
            force_exec = int(force_exec)
        except:
            force_exec = 2

        # 新增步骤
        if id == 0:
            # process_name下右键新增
            try:
                pid = int(pid)
            except:
                pid = None
                max_sort_from_pnode = \
                    Step.objects.exclude(state="9").filter(pnode_id=None, process_id=process_id).aggregate(Max("sort"))[
                        "sort__max"]
            else:
                max_sort_from_pnode = \
                    Step.objects.exclude(state="9").filter(pnode_id=pid).filter(process_id=process_id).aggregate(
                        Max("sort"))["sort__max"]

            # 当前没有父节点
            if max_sort_from_pnode or max_sort_from_pnode == 0:
                my_sort = max_sort_from_pnode + 1
            else:
                my_sort = 0

            step = Step()
            step.skip = skip
            step.approval = approval
            step.group = group
            step.rto_count_in = rto_count_in
            step.time = time if time else None
            step.name = name
            step.process_id = process_id
            step.pnode_id = pid
            step.sort = my_sort
            step.remark = remark
            step.force_exec = force_exec
            step.save()
            # last_id
            current_steps = Step.objects.filter(pnode_id=pid).exclude(state="9").order_by("sort").filter(
                process_id=process_id)
            last_id = current_steps[0].id
            for num, step in enumerate(current_steps):
                if num == 0:
                    step.last_id = ""
                else:
                    step.last_id = last_id
                last_id = step.id
                step.save()
            result = "保存成功。"
            data = step.id
        else:
            step = Step.objects.filter(id=id)
            if (len(step) > 0):
                step[0].name = name
                try:
                    time = int(time)
                    step[0].time = time
                except:
                    pass
                step[0].skip = skip
                step[0].approval = approval
                step[0].group = group
                step[0].rto_count_in = rto_count_in
                step[0].remark = remark
                step[0].force_exec = force_exec
                step[0].save()
                result = "保存成功。"
            else:
                result = "当前步骤不存在，请联系客服！"
        return JsonResponse({
            "result": result,
            "data": data
        })


def get_step_tree(parent, selectid):
    nodes = []
    children = parent.children.exclude(state="9").order_by("sort").all()
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = child.id
        node["children"] = get_step_tree(child, selectid)

        scripts = child.script_set.exclude(state="9").order_by("sort")
        script_string = ""
        for script in scripts:
            id_code_plus = str(script.id) + "+" + str(script.name) + "&"
            script_string += id_code_plus

        verify_items_string = ""
        verify_items = child.verifyitems_set.exclude(state="9")
        for verify_item in verify_items:
            id_name_plus = str(verify_item.id) + "+" + str(verify_item.name) + "&"
            verify_items_string += id_name_plus

        group_name = ""
        if child.group and child.group != " ":
            group_id = child.group
            try:
                group_id = int(group_id)
            except:
                raise Http404()

            group_name = Group.objects.filter(id=group_id)[0].name
        all_groups = Group.objects.exclude(state="9")
        group_string = " " + "+" + " -------------- " + "&"
        for group in all_groups:
            id_name_plus = str(group.id) + "+" + str(group.name) + "&"
            group_string += id_name_plus

        node["data"] = {"time": child.time, "approval": child.approval, "skip": child.skip, "group_name": group_name,
                        "group": child.group, "scripts": script_string, "allgroups": group_string,
                        "rto_count_in": child.rto_count_in, "remark": child.remark,
                        "verifyitems": verify_items_string, "force_exec": child.force_exec if child.force_exec else 2}
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def custom_step_tree(request):
    errors = []
    id = request.POST.get('id', "")
    p_step = ""
    pid = request.POST.get('pid', "")
    name = request.POST.get('name', "")
    process_id = request.POST.get("process", "")
    current_process = Process.objects.filter(id=process_id)
    if current_process:
        current_process = current_process[0]
    else:
        raise Http404()
    process_name = current_process.name

    if id == 0:
        selectid = pid
        title = "新建"
    else:
        selectid = id
        title = name

    try:
        if id == 0:
            sort = 1
            try:
                maxstep = Step.objects.filter(pnode=p_step).latest('sort').exclude(state="9")
                sort = maxstep.sort + 1
            except:
                pass
            funsave = Step()
            funsave.pnode = p_step
            funsave.name = name
            funsave.sort = sort
            funsave.save()
            title = name
            id = funsave.id
            selectid = id
        else:
            funsave = Step.objects.get(id=id)
            funsave.name = name
            funsave.save()
            title = name
    except:
        errors.append('保存失败。')

    treedata = []
    rootnodes = Step.objects.order_by("sort").filter(process_id=process_id, pnode=None).exclude(state="9")

    all_groups = Group.objects.exclude(state="9")
    group_string = "" + "+" + " -------------- " + "&"
    for group in all_groups:
        id_name_plus = str(group.id) + "+" + str(group.name) + "&"
        group_string += id_name_plus
    if len(rootnodes) > 0:
        for rootnode in rootnodes:
            root = {}
            scripts = rootnode.script_set.exclude(state="9").order_by("sort")
            script_string = ""
            for script in scripts:
                id_code_plus = str(script.id) + "+" + str(script.name) + "&"
                script_string += id_code_plus

            verify_items_string = ""
            verify_items = rootnode.verifyitems_set.exclude(state="9")
            for verify_item in verify_items:
                id_name_plus = str(verify_item.id) + "+" + str(verify_item.name) + "&"
                verify_items_string += id_name_plus
            root["text"] = rootnode.name
            root["id"] = rootnode.id
            group_name = ""

            try:
                group_id = int(rootnode.group)
                cur_group = Group.objects.get(id=group_id)

                group_name = cur_group.name
            except:
                pass

            root["data"] = {"time": rootnode.time, "approval": rootnode.approval, "skip": rootnode.skip,
                            "allgroups": group_string, "group": rootnode.group, "group_name": group_name,
                            "scripts": script_string, "errors": errors, "title": title,
                            "rto_count_in": rootnode.rto_count_in, "remark": rootnode.remark,
                            "verifyitems": verify_items_string,
                            "force_exec": rootnode.force_exec if rootnode.force_exec else 2}
            root["children"] = get_step_tree(rootnode, selectid)
            root["state"] = {"opened": True}
            treedata.append(root)
    process = {}
    process["text"] = process_name
    process["data"] = {"allgroups": group_string, "verify": "first_node"}
    process["children"] = treedata
    process["state"] = {"opened": True}
    return JsonResponse({"treedata": process})


@login_required
def processconfig(request, funid):
    process_id = request.GET.get("process_id", "")
    if process_id:
        process_id = int(process_id)

    processes = Process.objects.exclude(state="9").order_by("sort").exclude(Q(type=None) | Q(type=""))
    processlist = []
    for process in processes:
        processlist.append({"id": process.id, "code": process.code, "name": process.name})

    # 主机选项
    all_hosts_manage = HostsManage.objects.exclude(state="9")

    # commvault源端客户端
    all_origins = Origin.objects.exclude(state="9").order_by("utils__name")

    # 过滤本地commvaul接口脚本
    commv_path = os.path.join(os.path.join(settings.BASE_DIR, "faconstor"), "commvault_api")

    commv_file_list = os.listdir(commv_path)

    return render(request, 'processconfig.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                   "processlist": processlist, "process_id": process_id, "all_hosts_manage": all_hosts_manage,
                   "all_origins": all_origins, "commv_file_list": commv_file_list})


@login_required
def del_step(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        process_id = request.POST.get('process_id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        try:
            process_id = int(process_id)
        except:
            raise Http404()
        allsteps = Step.objects.filter(id=id)
        if (len(allsteps) > 0):
            sort = allsteps[0].sort
            pstep = allsteps[0].pnode
            allsteps[0].state = 9
            allsteps[0].save()
            sortsteps = Step.objects.filter(pnode=pstep).filter(sort__gt=sort).exclude(state="9").filter(
                process_id=process_id)
            if len(sortsteps) > 0:
                for sortstep in sortsteps:
                    try:
                        sortstep.sort = sortstep.sort - 1
                        sortstep.save()
                    except:
                        pass

            current_pnode_id = allsteps[0].pnode_id
            # last_id
            current_steps = Step.objects.filter(pnode_id=current_pnode_id).exclude(state="9").order_by(
                "sort").filter(
                process_id=process_id)
            if current_steps:
                last_id = current_steps[0].id
                for num, step in enumerate(current_steps):
                    if num == 0:
                        step.last_id = ""
                    else:
                        step.last_id = last_id
                    last_id = step.id
                    step.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


@login_required
def move_step(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        parent = request.POST.get('parent', '')
        old_parent = request.POST.get('old_parent', '')
        old_position = request.POST.get('old_position', '')
        position = request.POST.get('position', '')
        process_id = request.POST.get('process_id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        try:
            parent = int(parent)
        except:
            parent = None
        try:
            old_parent = int(old_parent)
        except:
            old_parent = None
        try:
            old_position = int(old_position)
        except:
            raise Http404()
        try:
            position = int(position)
        except:
            raise Http404()

        cur_step_obj = \
            Step.objects.filter(pnode_id=old_parent).filter(sort=old_position).filter(
                process_id=process_id).exclude(state="9")[0]
        cur_step_obj.sort = position
        cur_step_id = cur_step_obj.id
        cur_step_obj.save()
        # 同一pnode
        if parent == old_parent:
            # 向上拽
            steps_under_pnode = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                sort__gte=position,
                sort__lt=old_position).exclude(
                id=cur_step_id).filter(process_id=process_id)
            for step in steps_under_pnode:
                step.sort += 1
                step.save()

            # 向下拽
            steps_under_pnode = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                sort__gt=old_position, sort__lte=position).exclude(id=cur_step_id).filter(process_id=process_id)
            for step in steps_under_pnode:
                step.sort -= 1
                step.save()

        # 向其他节点拽
        else:
            # 原来pnode下
            old_steps = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                sort__gt=old_position).exclude(id=cur_step_id).filter(process_id=process_id)
            for step in old_steps:
                step.sort -= 1
                step.save()
            # 后来pnode下
            cur_steps = Step.objects.filter(pnode_id=parent).exclude(state="9").filter(sort__gte=position).exclude(
                id=cur_step_id).filter(process_id=process_id)
            for step in cur_steps:
                step.sort += 1
                step.save()

        # pnode
        if parent:
            parent_step = Step.objects.get(id=parent)
        else:
            parent_step = None
        mystep = Step.objects.get(id=id)
        try:
            mystep.pnode = parent_step
            mystep.save()
        except:
            pass

        # last_id
        old_steps = Step.objects.filter(pnode_id=old_parent).exclude(state="9").order_by("sort").filter(
            process_id=process_id)
        if old_steps:
            last_id = old_steps[0].id
            for num, step in enumerate(old_steps):
                if num == 0:
                    step.last_id = ""
                else:
                    step.last_id = last_id
                last_id = step.id
                step.save()
        after_steps = Step.objects.filter(pnode_id=parent).exclude(state="9").order_by("sort").filter(
            process_id=process_id)
        if after_steps:
            last_id = after_steps[0].id
            for num, step in enumerate(after_steps):
                if num == 0:
                    step.last_id = ""
                else:
                    step.last_id = last_id
                last_id = step.id
                step.save()

        if parent != old_parent:
            if parent == None:
                return HttpResponse(" ^ ")
            else:
                return HttpResponse(parent_step.name + "^" + str(parent_step.id))
        else:
            return HttpResponse("0")


@login_required
def get_all_groups(request):
    all_group_list = []
    all_groups = Group.objects.exclude(state="9")
    for num, group in enumerate(all_groups):
        group_info_dict = {
            "group_id": group.id,
            "group_name": group.name,
        }
        all_group_list.append(group_info_dict)
    return JsonResponse({"data": all_group_list})


@login_required
def process_design(request, funid):
    return render(request, "processdesign.html",
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})


@login_required
def process_data(request):
    result = []
    all_process = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")).order_by("sort").values()
    for process in all_process:
        param_list = []
        try:
            config = etree.XML(process['config'])

            param_el = config.xpath("//param")
            for v_param in param_el:
                param_list.append({
                    "param_name": v_param.attrib.get("param_name", ""),
                    "variable_name": v_param.attrib.get("variable_name", ""),
                    "param_value": v_param.attrib.get("param_value", ""),
                })
        except Exception as e:
            print(e)
        result.append({
            "process_id": process["id"],
            "process_code": process["code"],
            "process_name": process["name"],
            "process_remark": process["remark"],
            "process_sign": process["sign"],
            "process_rto": process["rto"],
            "process_rpo": process["rpo"],
            "process_sort": process["sort"],
            "process_color": process["color"],
            "type": process["type"],
            "variable_param_list": param_list,
        })
    return JsonResponse({"data": result})


@login_required
def process_save(request):
    if 'id' in request.POST:
        result = {}
        id = request.POST.get('id', '')
        code = request.POST.get('code', '')
        name = request.POST.get('name', '')
        remark = request.POST.get('remark', '')
        sign = request.POST.get('sign', '')
        rto = request.POST.get('rto', '')
        rpo = request.POST.get('rpo', '')
        sort = request.POST.get('sort', '')
        color = request.POST.get('color', '')
        type = request.POST.get('type', '')
        config = request.POST.get("config", "")

        try:
            id = int(id)
        except:
            raise Http404()
        if code.strip() == '':
            result["res"] = '预案编码不能为空。'
        else:
            if name.strip() == '':
                result["res"] = '预案名称不能为空。'
            else:
                if type.strip() == '':
                    result["res"] = '预案类型不能为空。'
                else:
                    if sign.strip() == '':
                        result["res"] = '是否签到不能为空。'
                    else:
                        # 流程参数
                        root = etree.Element("root")

                        if config:
                            config = json.loads(config)
                            # 动态参数
                            for c_config in config:
                                param_node = etree.SubElement(root, "param")
                                param_node.attrib["param_name"] = c_config["param_name"].strip()
                                param_node.attrib["variable_name"] = c_config["variable_name"].strip()
                                param_node.attrib["param_value"] = c_config["param_value"].strip()
                        config = etree.tounicode(root)

                        if id == 0:
                            all_process = Process.objects.filter(code=code).exclude(
                                state="9").exclude(Q(type=None) | Q(type=""))
                            if (len(all_process) > 0):
                                result["res"] = '预案编码:' + code + '已存在。'
                            else:
                                processsave = Process()
                                processsave.url = '/falconstor'
                                processsave.code = code
                                processsave.name = name
                                processsave.remark = remark
                                processsave.sign = sign
                                processsave.rto = rto if rto else None
                                processsave.rpo = rpo if rpo else None
                                processsave.sort = sort if sort else None
                                processsave.color = color
                                processsave.type = type
                                processsave.config = config
                                processsave.save()
                                result["res"] = "保存成功。"
                                result["data"] = processsave.id
                        else:
                            all_process = Script.objects.filter(code=code).exclude(
                                id=id).exclude(state="9")
                            if (len(all_process) > 0):
                                result["res"] = '预案编码:' + code + '已存在。'
                            else:
                                try:
                                    processsave = Process.objects.get(id=id)
                                    processsave.code = code
                                    processsave.name = name
                                    processsave.remark = remark
                                    processsave.sign = sign
                                    processsave.rto = rto if rto else None
                                    processsave.rpo = rpo if rpo else None
                                    processsave.sort = sort if sort else None
                                    processsave.color = color
                                    processsave.type = type
                                    processsave.config = config
                                    processsave.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = processsave.id
                                except:
                                    result["res"] = "修改失败。"
    return HttpResponse(json.dumps(result))


@login_required
def process_del(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        process = Process.objects.get(id=id)
        process.state = "9"
        process.save()

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def falconstorswitch(request, process_id):
    all_wrapper_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=None).order_by(
        "sort")
    wrapper_step_list = []
    num_to_char_choices = {
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七",
        "8": "八",
        "9": "九",
    }
    for num, wrapper_step in enumerate(all_wrapper_steps):
        wrapper_step_dict = {}
        wrapper_step_dict["wrapper_step_name"] = num_to_char_choices[
                                                     "{0}".format(str(num + 1))] + "." + wrapper_step.name
        wrapper_step_group_id = wrapper_step.group
        try:
            wrapper_step_group_id = int(wrapper_step_group_id)
        except:
            wrapper_step_group_id = None
        wrapper_step_group = Group.objects.filter(id=wrapper_step_group_id)
        if wrapper_step_group:
            wrapper_step_group_name = wrapper_step_group[0].name
        else:
            wrapper_step_group_name = ""
        wrapper_step_dict["wrapper_step_group_name"] = wrapper_step_group_name

        wrapper_script_list = []
        all_wrapper_scripts = wrapper_step.script_set.exclude(state="9").order_by("sort")
        for wrapper_script in all_wrapper_scripts:
            wrapper_script_dict = {
                "wrapper_script_name": wrapper_script.name
            }
            wrapper_script_list.append(wrapper_script_dict)
            wrapper_step_dict["wrapper_script_list"] = wrapper_script_list

        wrapper_verify_list = []
        all_wrapper_verifys = wrapper_step.verifyitems_set.exclude(state="9")
        for wrapper_verify in all_wrapper_verifys:
            wrapper_verify_dict = {
                "wrapper_verify_name": wrapper_verify.name
            }
            wrapper_verify_list.append(wrapper_verify_dict)
            wrapper_step_dict["wrapper_verify_list"] = wrapper_verify_list

        pnode_id = wrapper_step.id
        inner_step_list = []
        all_inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=pnode_id).order_by(
            "sort")
        for inner_step in all_inner_steps:
            inner_step_dict = {}
            inner_step_dict["inner_step_name"] = inner_step.name

            inner_step_group_id = inner_step.group
            try:
                inner_step_group_id = int(inner_step_group_id)
            except:
                inner_step_group_id = None
            inner_step_group = Group.objects.filter(id=inner_step_group_id)
            if inner_step_group:
                inner_step_group_name = inner_step_group[0].name
            else:
                inner_step_group_name = ""
            inner_step_dict["inner_step_group_name"] = inner_step_group_name

            inner_script_list = []
            all_inner_scripts = inner_step.script_set.exclude(state="9").order_by("sort")
            for inner_script in all_inner_scripts:
                inner_script_dict = {
                    "inner_script_name": inner_script.name
                }
                inner_script_list.append(inner_script_dict)

            inner_verify_list = []
            all_inner_verifys = inner_step.verifyitems_set.exclude(state="9")
            for inner_verify in all_inner_verifys:
                inner_verify_dict = {
                    "inner_verify_name": inner_verify.name
                }
                inner_verify_list.append(inner_verify_dict)

            inner_step_dict["inner_verify_list"] = inner_verify_list
            inner_step_dict["inner_script_list"] = inner_script_list
            inner_step_list.append(inner_step_dict)

        wrapper_step_dict["inner_step_list"] = inner_step_list

        wrapper_step_list.append(wrapper_step_dict)

    # 计划流程
    plan_process_run = ProcessRun.objects.filter(process_id=process_id, state="PLAN")
    if plan_process_run:
        plan_process_run = plan_process_run[0]
        plan_process_run_id = plan_process_run.id
    else:
        plan_process_run_id = ""

    # 根据url寻找到funid
    falconstor_url = "/falconstorswitch/{0}".format(process_id)

    c_fun = Fun.objects.filter(url=falconstor_url)
    if c_fun.exists():
        c_fun = c_fun[0]
        funid = str(c_fun.id)
    else:
        return Http404()

    # 预案类型
    type = ''
    try:
        process = Process.objects.get(id=process_id)
    except Process.DoesNotExist as e:
        print(e)
    else:
        type = process.type

    # commvault目标客户端
    all_targets = Target.objects.exclude(state="9")

    # commvault源客户端
    all_steps = Step.objects.exclude(state="9").filter(process_id=process_id).prefetch_related(
        "script_set", "script_set__origin", "script_set__origin__target")

    target_id = ""
    origin = ""
    data_path = ""
    copy_priority = ""
    db_open = ""
    for cur_step in all_steps:
        # all_scripts = Script.objects.filter(step_id=cur_step.id).exclude(state="9").select_related("origin")
        all_scripts = cur_step.script_set.exclude(state="9")
        for cur_script in all_scripts:
            if cur_script.origin:
                origin = cur_script.origin
                target_id = cur_script.origin.target.id
                data_path = cur_script.origin.data_path
                copy_priority = cur_script.origin.copy_priority
                db_open = cur_script.origin.db_open
                break
    return render(request, 'falconstorswitch.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                   "wrapper_step_list": wrapper_step_list, "process_id": process_id, "type": type,
                   "data_path": data_path,
                   "plan_process_run_id": plan_process_run_id, "all_targets": all_targets, "origin": origin,
                   "target_id": target_id, "copy_priority": copy_priority, "db_open": db_open})


@login_required
def falconstorswitchdata(request):
    result = []
    process_id = request.GET.get("process_id", "")
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

    try:
        with connection.cursor() as cursor:
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url, p.type from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state != 'REJECT' and r.process_id = {0} order by r.starttime desc;
            """.format(process_id)

            cursor.execute(exec_sql)
            rows = cursor.fetchall()
            for processrun_obj in rows:
                create_users = processrun_obj[2] if processrun_obj[2] else ""
                create_user_objs = User.objects.filter(username=create_users)
                create_user_fullname = create_user_objs[0].userinfo.fullname if create_user_objs else ""

                result.append({
                    "starttime": processrun_obj[0].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[0] else "",
                    "endtime": processrun_obj[1].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[1] else "",
                    "createuser": create_user_fullname,
                    "state": state_dict["{0}".format(processrun_obj[3])] if processrun_obj[3] else "",
                    "process_id": processrun_obj[4] if processrun_obj[4] else "",
                    "processrun_id": processrun_obj[5] if processrun_obj[5] else "",
                    "run_reason": processrun_obj[6][:20] if processrun_obj[6] else "",
                    "process_name": processrun_obj[7] if processrun_obj[7] else "",
                    "process_url": processrun_obj[8] if processrun_obj[8] else "",
                    "process_type": processrun_obj[9] if processrun_obj[9] else ""
                })
    finally:
        connection.close()

    return JsonResponse({"data": result})


@login_required
def falconstorrun(request):
    result = {}
    processid = request.POST.get('processid', '')
    run_person = request.POST.get('run_person', '')
    run_time = request.POST.get('run_time', '')
    run_reason = request.POST.get('run_reason', '')

    target = request.POST.get('target', '')
    recovery_time = request.POST.get('recovery_time', '')
    browseJobId = request.POST.get('browseJobId', '')
    data_path = request.POST.get('data_path', '')
    copy_priority = request.POST.get('copy_priority', '')
    db_open = request.POST.get('db_open', '')

    origin = request.POST.get('origin', '')
    try:
        processid = int(processid)
    except:
        raise Http404()
    process = Process.objects.filter(id=processid).exclude(state="9").exclude(Q(type=None) | Q(type=""))
    if not process.exists():
        result["res"] = '流程启动失败，该流程不存在。'
    else:
        # Commvault相关
        if process[0].type.upper() == 'COMMVAULT':
            try:
                origin = int(origin)
            except:
                return JsonResponse({"res": "流程步骤中未添加Commvault接口，导致源客户端未空。"})

            try:
                target = int(target)
            except:
                return JsonResponse({"res": "目标客户端未选择。"})

        running_process = ProcessRun.objects.filter(process=process[0], state__in=["RUN", "ERROR"])
        if running_process.exists():
            result["res"] = '流程启动失败，该流程正在进行中，请勿重复启动。'
        else:
            planning_process = ProcessRun.objects.filter(process=process[0], state="PLAN")
            if planning_process.exists():
                result["res"] = '流程启动失败，计划流程未执行，务必先完成计划流程。'
            else:
                myprocessrun = ProcessRun()
                myprocessrun.process = process[0]
                myprocessrun.starttime = datetime.datetime.now()
                myprocessrun.creatuser = request.user.username
                myprocessrun.run_reason = run_reason
                myprocessrun.state = "RUN"

                if process[0].type.upper() == 'COMMVAULT':
                    # Commvault 相关
                    myprocessrun.target_id = target
                    myprocessrun.browse_job_id = browseJobId
                    myprocessrun.data_path = data_path
                    myprocessrun.copy_priority = copy_priority
                    myprocessrun.db_open = db_open
                    myprocessrun.origin_id = origin
                    myprocessrun.recover_time = datetime.datetime.strptime(recovery_time,
                                                                           "%Y-%m-%d %H:%M:%S") if recovery_time else None
                    # 是否回滚归档日志
                    log_restore = 1
                    origin = Origin.objects.filter(id=origin)
                    if origin:
                        log_restore = origin[0].log_restore
                    myprocessrun.log_restore = log_restore

                myprocessrun.save()
                mystep = process[0].step_set.exclude(state="9").order_by("sort")
                if not mystep.exists():
                    result["res"] = '流程启动失败，没有找到可用步骤。'
                else:
                    for step in mystep:
                        mysteprun = StepRun()
                        mysteprun.step = step
                        mysteprun.processrun = myprocessrun
                        mysteprun.state = "EDIT"
                        mysteprun.save()

                        myscript = step.script_set.exclude(state="9").order_by("sort")
                        for script in myscript:
                            myscriptrun = ScriptRun()
                            myscriptrun.script = script
                            myscriptrun.steprun = mysteprun
                            myscriptrun.state = "EDIT"
                            myscriptrun.save()

                        myverifyitems = step.verifyitems_set.exclude(state="9")
                        for verifyitems in myverifyitems:
                            myverifyitemsrun = VerifyItemsRun()
                            myverifyitemsrun.verify_items = verifyitems
                            myverifyitemsrun.steprun = mysteprun
                            myverifyitemsrun.save()

                    allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                        "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                    if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                        # 将当前流程改成SIGN
                        c_process_run_id = myprocessrun.id
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
                                myprocesstask.processrun = myprocessrun
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = request.user.username
                                myprocesstask.receiveauth = group["group"]
                                myprocesstask.type = "SIGN"
                                myprocesstask.state = "0"
                                myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                                myprocesstask.save()
                            except:
                                pass
                        result["res"] = "新增成功。"
                        result["data"] = "/"

                    else:
                        prosssigns = ProcessTask.objects.filter(processrun=myprocessrun, state="0")
                        if len(prosssigns) <= 0:
                            myprocess = myprocessrun.process
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = myprocessrun
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.type = "INFO"
                            myprocesstask.logtype = "START"
                            myprocesstask.state = "1"
                            myprocesstask.senduser = request.user.username
                            myprocesstask.content = "流程启动。"
                            myprocesstask.save()

                            exec_process.delay(myprocessrun.id)
                            result["res"] = "新增成功。"
                            result["data"] = "/processindex/" + str(myprocessrun.id)
    return JsonResponse(result)


@login_required
def falconstor_run_invited(request):
    result = {}
    process_id = request.POST.get('processid', '')
    run_person = request.POST.get('run_person', '')
    run_time = request.POST.get('run_time', '')
    run_reason = request.POST.get('run_reason', '')
    plan_process_run_id = request.POST.get('plan_process_run_id', '')

    current_process_run = ProcessRun.objects.filter(id=plan_process_run_id)

    if current_process_run:
        current_process_run = current_process_run[0]

        if current_process_run.state == "RUN":
            result["res"] = '请勿重复启动该流程。'
        else:
            current_process_run.starttime = datetime.datetime.now()
            current_process_run.creatuser = request.user.username
            current_process_run.run_reason = run_reason
            current_process_run.state = "RUN"
            current_process_run.DataSet_id = 89
            current_process_run.save()

            process = Process.objects.filter(id=process_id).exclude(state="9").exclude(Q(type=None) | Q(type=""))

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
                        myprocesstask.senduser = request.user.username
                        myprocesstask.receiveauth = group["group"]
                        myprocesstask.type = "SIGN"
                        myprocesstask.state = "0"
                        myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                        myprocesstask.save()
                    except:
                        pass
                result["res"] = "新增成功。"
                result["data"] = "/"

            else:
                prosssigns = ProcessTask.objects.filter(processrun=current_process_run, state="0")
                if len(prosssigns) <= 0:
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = current_process_run
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.type = "INFO"
                    myprocesstask.logtype = "START"
                    myprocesstask.state = "1"
                    myprocesstask.senduser = request.user.username
                    myprocesstask.content = "流程启动。"
                    myprocesstask.save()

                    exec_process.delay(current_process_run.id)
                    result["res"] = "新增成功。"
                    result["data"] = process[0].url + "/" + str(current_process_run.id)
    else:
        result["res"] = '流程启动异常，请联系客服。'

    return HttpResponse(json.dumps(result))


@login_required
def walkthrough(request, funid):
    processes = Process.objects.exclude(state="9").order_by("sort").exclude(Q(type=None) | Q(type=""))
    processlist = []
    for process in processes:
        processlist.append({"id": process.id, "code": process.code, "name": process.name})

    return render(request, 'walkthrough.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                   "processlist": processlist})


@login_required
def walkthroughdata(request):
    result = []
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
        "": "",
    }
    walkthroughs = Walkthrough.objects.order_by('-id').exclude(state='9').exclude(state='REJECT')
    for walkthrough in walkthroughs:
        create_users = walkthrough.creatuser if walkthrough.creatuser else ""
        create_user_objs = User.objects.filter(username=create_users)
        create_user_fullname = create_user_objs[0].userinfo.fullname if create_user_objs else ""
        processes = ""
        processrunes = walkthrough.processrun_set.exclude(state="9").exclude(state='REJECT')
        process_name_list = []
        for processrun in processrunes:
            processes += str(processrun.process.id) + "^"
            process_name_list.append(processrun.process.name)

        result.append({
            "starttime": walkthrough.starttime.strftime('%Y-%m-%d %H:%M:%S') if walkthrough.starttime else "",
            "endtime": walkthrough.endtime.strftime('%Y-%m-%d %H:%M:%S') if walkthrough.endtime else "",
            "createtime": walkthrough.createtime.strftime('%Y-%m-%d %H:%M:%S') if walkthrough.createtime else "",
            "createuser": create_user_fullname,
            "state": state_dict["{0}".format(walkthrough.state)] if walkthrough.state else "",
            "walkthrough_id": walkthrough.id if walkthrough.id else "",
            "purpose": walkthrough.purpose if walkthrough.purpose else "",
            "walkthrough_name": walkthrough.name if walkthrough.name else "",
            "processes": processes,
            "process_name_list": process_name_list
        })
    return JsonResponse({"data": result})


@login_required
def walkthroughsave(request):
    result = {}
    id = request.POST.get("id", "")
    name = request.POST.get("name", "")
    start_time = request.POST.get("start_time", "")
    purpose = request.POST.get("purpose", "")
    end_time = request.POST.get("end_time", "")
    processes = request.POST.get('processes', '')
    processes = processes.split("*!-!*")
    processes.remove("")
    try:
        id = int(id)
    except:
        raise Http404()
    # 准备流程PLAN
    if name:
        if processes:
            if start_time:
                if end_time:
                    if id == 0:
                        walkthrough = Walkthrough.objects.filter(state__in=["PLAN", "RUN", "ERROR"])
                        if (len(walkthrough) > 0):
                            result["res"] = '演练计划创建失败，已经存在演练计划，务必先完成该计划。'
                        else:
                            walkthrough = Walkthrough()
                            walkthrough.name = name
                            walkthrough.createtime = datetime.datetime.now()
                            walkthrough.creatuser = request.user.username
                            walkthrough.state = "PLAN"
                            walkthrough.purpose = purpose
                            walkthrough.starttime = start_time
                            walkthrough.endtime = end_time
                            walkthrough.save()

                            for process_id in processes:
                                process = Process.objects.filter(id=int(process_id)).exclude(state="9").exclude(
                                    Q(type=None) | Q(type=""))
                                myprocessrun = ProcessRun()
                                myprocessrun.walkthrough = walkthrough
                                myprocessrun.process = process[0]
                                myprocessrun.state = "PLAN"
                                myprocessrun.starttime = start_time
                                myprocessrun.save()
                                current_process_run_id = myprocessrun.id

                                mystep = process[0].step_set.exclude(state="9").order_by("sort")
                                for step in mystep:
                                    mysteprun = StepRun()
                                    mysteprun.step = step
                                    mysteprun.processrun = myprocessrun
                                    mysteprun.state = "EDIT"
                                    mysteprun.save()

                                    myscript = step.script_set.exclude(state="9").order_by("sort")
                                    for script in myscript:
                                        myscriptrun = ScriptRun()
                                        myscriptrun.script = script
                                        myscriptrun.steprun = mysteprun
                                        myscriptrun.state = "EDIT"
                                        myscriptrun.save()

                                    myverifyitems = step.verifyitems_set.exclude(state="9")
                                    for verifyitems in myverifyitems:
                                        myverifyitemsrun = VerifyItemsRun()
                                        myverifyitemsrun.verify_items = verifyitems
                                        myverifyitemsrun.steprun = mysteprun
                                        myverifyitemsrun.save()

                                # 生成邀请任务信息
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun_id = current_process_run_id
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = request.user.username
                                myprocesstask.type = "INFO"
                                myprocesstask.logtype = "PLAN"
                                myprocesstask.state = "1"
                                myprocesstask.content = "创建流程计划。"
                                myprocesstask.save()

                            mywalkthroughtask = ProcessTask()
                            mywalkthroughtask.walkthrough = walkthrough
                            mywalkthroughtask.starttime = datetime.datetime.now()
                            mywalkthroughtask.senduser = request.user.username
                            mywalkthroughtask.type = "INFO"
                            mywalkthroughtask.logtype = "PLAN"
                            mywalkthroughtask.state = "1"
                            mywalkthroughtask.content = "创建演练计划。"
                            mywalkthroughtask.save()

                            result["data"] = walkthrough.id
                            result["res"] = "演练计划保存成功，待开启流程。"
                    else:
                        walkthrough = Walkthrough.objects.get(id=id)
                        walkthrough.name = name
                        walkthrough.createtime = datetime.datetime.now()
                        walkthrough.creatuser = request.user.username
                        walkthrough.state = "PLAN"
                        walkthrough.purpose = purpose
                        walkthrough.starttime = start_time
                        walkthrough.endtime = end_time
                        walkthrough.save()

                        processruns = ProcessRun.objects.filter(walkthrough=walkthrough).exclude(
                            state__in=["9", "REJECT"])
                        for processrun in processruns:
                            id = str(processrun.id)
                            if id not in processes:
                                processrun.state = '9'
                                processrun.save()

                        for process_id in processes:
                            process = Process.objects.filter(id=int(process_id)).exclude(state="9").exclude(
                                Q(type=None) | Q(type=""))
                            curprocessrun = ProcessRun.objects.filter(walkthrough=walkthrough,
                                                                      process=process[0]).exclude(
                                state__in=["9", "REJECT"])
                            if len(curprocessrun) == 0:
                                myprocessrun = ProcessRun()
                                myprocessrun.walkthrough = walkthrough
                                myprocessrun.process = process[0]
                                myprocessrun.state = "PLAN"
                                myprocessrun.starttime = start_time
                                myprocessrun.save()
                                current_process_run_id = myprocessrun.id

                                mystep = process[0].step_set.exclude(state="9").order_by("sort")
                                for step in mystep:
                                    mysteprun = StepRun()
                                    mysteprun.step = step
                                    mysteprun.processrun = myprocessrun
                                    mysteprun.state = "EDIT"
                                    mysteprun.save()

                                    myscript = step.script_set.exclude(state="9").order_by("sort")
                                    for script in myscript:
                                        myscriptrun = ScriptRun()
                                        myscriptrun.script = script
                                        myscriptrun.steprun = mysteprun
                                        myscriptrun.state = "EDIT"
                                        myscriptrun.save()

                                    myverifyitems = step.verifyitems_set.exclude(state="9")
                                    for verifyitems in myverifyitems:
                                        myverifyitemsrun = VerifyItemsRun()
                                        myverifyitemsrun.verify_items = verifyitems
                                        myverifyitemsrun.steprun = mysteprun
                                        myverifyitemsrun.save()

                                # 生成邀请任务信息
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun_id = current_process_run_id
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = request.user.username
                                myprocesstask.type = "INFO"
                                myprocesstask.logtype = "PLAN"
                                myprocesstask.state = "1"
                                myprocesstask.content = "创建流程计划。"
                                myprocesstask.save()

                        mywalkthroughtask = ProcessTask()
                        mywalkthroughtask.walkthrough = walkthrough
                        mywalkthroughtask.starttime = datetime.datetime.now()
                        mywalkthroughtask.senduser = request.user.username
                        mywalkthroughtask.type = "INFO"
                        mywalkthroughtask.logtype = "PLAN"
                        mywalkthroughtask.state = "1"
                        mywalkthroughtask.content = "创建演练计划。"
                        mywalkthroughtask.save()

                        result["data"] = walkthrough.id
                        result["res"] = "演练计划保存成功，待开启流程。"
                else:
                    result["res"] = "演练结束时间必须填写！"
            else:
                result["res"] = "演练开始时间必须填写！"
        else:
            result["res"] = "必须选择演练系统填写！"
    else:
        result["res"] = "演练清楚必须填写！"

    return JsonResponse(result)


@login_required
def reject_walkthrough(request):
    id = request.POST.get("id", "")
    walkthrough = Walkthrough.objects.filter(id=id)
    if walkthrough:
        walkthrough = walkthrough[0]
        walkthrough.state = "REJECT"
        walkthrough.save()
        processrunes = walkthrough.processrun_set.exclude(state="9").exclude(state='REJECT')
        for processrun in processrunes:
            processrun.state = "REJECT"
            processrun.save()

            # 生成取消任务信息
            myprocesstask = ProcessTask()
            myprocesstask.processrun_id = processrun.id
            myprocesstask.starttime = datetime.datetime.now()
            myprocesstask.senduser = request.user.username
            myprocesstask.type = "INFO"
            myprocesstask.logtype = "REJECT"
            myprocesstask.state = "1"
            myprocesstask.content = "取消演练计划。"
            myprocesstask.save()

        result = "取消演练计划成功！"
    else:
        result = "演练计划不存在，取消失败！"
    return JsonResponse({"res": result})


@login_required
def walkthroughdel(request):
    id = request.POST.get("id", "")

    try:
        id = int(id)
    except:
        raise Http404()

    walkthrough = Walkthrough.objects.filter(id=id)
    if walkthrough:
        walkthrough = walkthrough[0]
        walkthrough.state = "9"
        walkthrough.save()

        ################
        # 删除关联流程 #
        ################
        all_process_run = walkthrough.processrun_set.exclude(state="9")
        if all_process_run.exists():
            all_process_run.update(state="9")

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def falconstor(request, offset, funid):
    id = 0
    try:
        id = int(offset)
    except:
        raise Http404()

    # 查看当前流程状态
    current_process_run = ProcessRun.objects.filter(id=offset)
    if current_process_run:
        current_process_run = current_process_run[0]
        current_run_state = current_process_run.state
    else:
        current_run_state = ""

    return render(request, 'falconstor.html',
                  {'username': request.user.userinfo.fullname, "process": id,
                   "current_run_state": current_run_state,
                   "pagefuns": getpagefuns(funid, request)})


def getchildrensteps(processrun, curstep):
    childresult = []
    steplist = Step.objects.exclude(state="9").filter(pnode=curstep).order_by("sort")
    for step in steplist:
        runid = 0
        starttime = ""
        endtime = ""
        operator = ""
        parameter = ""
        runresult = ""
        explain = ""
        state = ""
        steprunlist = StepRun.objects.exclude(state="9").filter(processrun=processrun, step=step)
        if len(steprunlist) > 0:
            runid = steprunlist[0].id
            try:
                starttime = steprunlist[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            try:
                endtime = steprunlist[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            rto = ""
            if steprunlist[0].state == "DONE":
                try:
                    current_delta_time = (steprunlist[0].endtime - steprunlist[0].starttime).total_seconds()
                    m, s = divmod(current_delta_time, 60)
                    h, m = divmod(m, 60)
                    rto = "%d时%02d分%02d秒" % (h, m, s)
                except:
                    pass
            else:
                start_time = steprunlist[0].starttime.replace(tzinfo=None) if steprunlist[0].starttime else ""
                current_time = datetime.datetime.now()
                current_delta_time = (current_time - start_time).total_seconds() if current_time and start_time else 0
                m, s = divmod(current_delta_time, 60)
                h, m = divmod(m, 60)
                rto = "%d时%02d分%02d秒" % (h, m, s)
            operator = steprunlist[0].operator
            if operator is not None and operator != "":
                try:
                    curuser = User.objects.get(username=operator)
                    operator = curuser.userinfo.fullname
                except:
                    pass
            else:
                operator = ""
            parameter = steprunlist[0].parameter
            runresult = steprunlist[0].result
            explain = steprunlist[0].explain
            state = steprunlist[0].state
            note = steprunlist[0].note
            group = step.group
            try:
                curgroup = Group.objects.get(id=int(group))
                group = curgroup.name
            except:
                pass
        scripts = []
        scriptlist = Script.objects.exclude(state="9").filter(step=step).order_by("sort")
        for script in scriptlist:
            runscriptid = 0
            scriptstarttime = ""
            scriptendtime = ""
            scriptoperator = ""
            scriptrunresult = ""
            scriptexplain = ""
            scriptrunlog = ""
            scriptstate = ""
            if len(steprunlist) > 0:
                scriptrunlist = ScriptRun.objects.exclude(state="9").filter(steprun=steprunlist[0], script=script)
                if len(scriptrunlist) > 0:
                    runscriptid = scriptrunlist[0].id
                    try:
                        scriptstarttime = scriptrunlist[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    try:
                        scriptendtime = scriptrunlist[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    scriptoperator = scriptrunlist[0].operator
                    scriptrunlog = scriptrunlist[0].runlog
                    scriptrunresult = scriptrunlist[0].result
                    scriptexplain = scriptrunlist[0].explain
                    scriptstate = scriptrunlist[0].state
            scripts.append({"id": script.id, "code": script.code, "name": script.name, "runscriptid": runscriptid,
                            "scriptstarttime": scriptstarttime,
                            "scriptendtime": scriptendtime, "scriptoperator": scriptoperator,
                            "scriptrunresult": scriptrunresult, "scriptexplain": scriptexplain,
                            "scriptrunlog": scriptrunlog, "scriptstate": scriptstate})

        verifyitems = []
        verifyitemslist = VerifyItems.objects.exclude(state="9").filter(step=step)
        for verifyitem in verifyitemslist:
            runverifyitemid = 0
            has_verified = ""
            verifyitemstate = ""
            if len(steprunlist) > 0:
                verifyitemsrunlist = VerifyItemsRun.objects.exclude(state="9").filter(steprun=steprunlist[0],
                                                                                      verify_items=verifyitem)
                if len(verifyitemsrunlist) > 0:
                    runverifyitemid = verifyitemsrunlist[0].id
                    has_verified = verifyitemsrunlist[0].has_verified
                    verifyitemstate = verifyitemsrunlist[0].state
            verifyitems.append(
                {"id": verifyitem.id, "name": verifyitem.name, "runverifyitemid": runverifyitemid,
                 "has_verified": has_verified,
                 "verifyitemstate": verifyitemstate})

        childresult.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                            "skip": step.skip, "group": group, "time": step.time, "runid": runid,
                            "starttime": starttime, "endtime": endtime, "operator": operator,
                            "parameter": parameter, "runresult": runresult,
                            "explain": explain, "state": state, "scripts": scripts, "verifyitems": verifyitems,
                            "note": note, "rto": rto, "children": getchildrensteps(processrun, step)})
    return childresult


@login_required
def getrunsetps(request):
    if request.method == 'POST':
        processresult = {}
        result = []
        process_name = ""
        process_state = ""
        process_starttime = ""
        process_endtime = ""
        process_note = ""
        process_rto = ""
        processrun = request.POST.get('process', '')
        processrun = int(processrun)
        processruns = ProcessRun.objects.exclude(state="9").filter(id=processrun)
        if len(processruns) > 0:
            process_name = processruns[0].process.name
            process_state = processruns[0].state
            process_note = processruns[0].note
            try:
                process_starttime = processruns[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            try:
                process_endtime = processruns[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            if process_state == "DONE" or process_state == "STOP":
                try:
                    current_delta_time = (processruns[0].endtime - processruns[0].starttime).total_seconds()
                    m, s = divmod(current_delta_time, 60)
                    h, m = divmod(m, 60)
                    process_rto = "%d时%02d分%02d秒" % (h, m, s)
                except:
                    pass
            else:
                start_time = processruns[0].starttime.replace(tzinfo=None)
                current_time = datetime.datetime.now()
                current_delta_time = (current_time - start_time).total_seconds()
                m, s = divmod(current_delta_time, 60)
                h, m = divmod(m, 60)
                process_rto = "%d时%02d分%02d秒" % (h, m, s)

            # 当前流程所有任务
            current_process_task_info = get_c_process_run_tasks(processrun)

            processresult["current_process_task_info"] = current_process_task_info
            processresult["step"] = result
            processresult["process_name"] = process_name
            processresult["process_state"] = process_state
            processresult["process_starttime"] = process_starttime
            processresult["process_endtime"] = process_endtime
            processresult["process_note"] = process_note
            processresult["process_rto"] = process_rto

            steplist = Step.objects.exclude(state="9").filter(process=processruns[0].process, pnode=None).order_by(
                "sort")
            for step in steplist:
                runid = 0
                starttime = ""
                endtime = ""
                operator = ""
                parameter = ""
                runresult = ""
                explain = ""
                state = ""
                group = ""
                note = ""
                rto = 0
                steprunlist = StepRun.objects.exclude(state="9").filter(processrun=processruns[0], step=step)
                if len(steprunlist) > 0:
                    runid = steprunlist[0].id
                    try:
                        starttime = steprunlist[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    try:
                        endtime = steprunlist[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    rto = ""
                    if steprunlist[0].state == "DONE":
                        try:
                            current_delta_time = (steprunlist[0].endtime - steprunlist[0].starttime).total_seconds()
                            m, s = divmod(current_delta_time, 60)
                            h, m = divmod(m, 60)
                            rto = "%d时%02d分%02d秒" % (h, m, s)
                        except:
                            pass
                    else:
                        start_time = steprunlist[0].starttime.replace(tzinfo=None) if steprunlist[
                            0].starttime else ""
                        current_time = datetime.datetime.now()
                        current_delta_time = (
                                current_time - start_time).total_seconds() if current_time and start_time else 0
                        m, s = divmod(current_delta_time, 60)
                        h, m = divmod(m, 60)
                        rto = "%d时%02d分%02d秒" % (h, m, s)
                    operator = steprunlist[0].operator
                    if operator is not None and operator != "":
                        try:
                            curuser = User.objects.get(username=operator)
                            operator = curuser.userinfo.fullname
                        except:
                            pass
                    else:
                        operator = ""
                    parameter = steprunlist[0].parameter
                    runresult = steprunlist[0].result
                    explain = steprunlist[0].explain
                    state = steprunlist[0].state
                    note = steprunlist[0].note
                    group = step.group
                    try:
                        curgroup = Group.objects.get(id=int(group))
                        group = curgroup.name
                    except:
                        pass
                scripts = []
                scriptlist = Script.objects.exclude(state="9").filter(step=step).order_by("sort")
                for script in scriptlist:
                    runscriptid = 0
                    scriptstarttime = ""
                    scriptendtime = ""
                    scriptoperator = ""
                    scriptrunresult = ""
                    scriptexplain = ""
                    scriptrunlog = ""
                    scriptstate = ""
                    if len(steprunlist) > 0:
                        scriptrunlist = ScriptRun.objects.exclude(state="9").filter(steprun=steprunlist[0],
                                                                                    script=script)
                        if len(scriptrunlist) > 0:
                            runscriptid = scriptrunlist[0].id
                            try:
                                scriptstarttime = scriptrunlist[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                            try:
                                scriptendtime = scriptrunlist[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                            scriptoperator = scriptrunlist[0].operator
                            scriptrunlog = scriptrunlist[0].runlog
                            scriptrunresult = scriptrunlist[0].result
                            scriptexplain = scriptrunlist[0].explain
                            scriptstate = scriptrunlist[0].state
                    scripts.append(
                        {"id": script.id, "code": script.code, "name": script.name, "runscriptid": runscriptid,
                         "scriptstarttime": scriptstarttime,
                         "scriptendtime": scriptendtime, "scriptoperator": scriptoperator,
                         "scriptrunresult": scriptrunresult, "scriptexplain": scriptexplain,
                         "scriptrunlog": scriptrunlog, "scriptstate": scriptstate})
                verifyitems = []
                verifyitemslist = VerifyItems.objects.exclude(state="9").filter(step=step)
                for verifyitem in verifyitemslist:
                    runverifyitemid = 0
                    has_verified = ""
                    verifyitemstate = ""
                    if len(steprunlist) > 0:
                        verifyitemsrunlist = VerifyItemsRun.objects.exclude(state="9").filter(
                            steprun=steprunlist[0],
                            verify_items=verifyitem)
                        if len(verifyitemsrunlist) > 0:
                            runverifyitemid = verifyitemsrunlist[0].id
                            has_verified = verifyitemsrunlist[0].has_verified
                            verifyitemstate = verifyitemsrunlist[0].state
                    verifyitems.append(
                        {"id": verifyitem.id, "name": verifyitem.name, "runverifyitemid": runverifyitemid,
                         "has_verified": has_verified,
                         "verifyitemstate": verifyitemstate})

                result.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                               "skip": step.skip, "group": group, "time": step.time, "runid": runid,
                               "starttime": starttime, "endtime": endtime, "operator": operator,
                               "parameter": parameter, "runresult": runresult, "explain": explain,
                               "state": state, "scripts": scripts, "verifyitems": verifyitems,
                               "note": note, "rto": rto, "children": getchildrensteps(processruns[0], step)})
        return HttpResponse(json.dumps(processresult))


@login_required
def falconstorcontinue(request):
    result = {}
    process = request.POST.get('process', '')
    try:
        process = int(process)
    except:
        raise Http404()
    exec_process.delay(process, if_repeat=True)
    result["res"] = "执行成功。"

    current_process_run = ProcessRun.objects.filter(id=process)
    if current_process_run:
        current_process_run = current_process_run[0]

        all_tasks_ever = current_process_run.processtask_set.filter(state="0")
        if all_tasks_ever:
            for task in all_tasks_ever:
                task.endtime = datetime.datetime.now()
                task.state = "1"
                task.save()
    else:
        result["res"] = "流程不存在。"
    return HttpResponse(json.dumps(result))


@login_required
def get_celery_tasks_info(request):
    task_url = "http://127.0.0.1:5555/api/tasks"
    try:
        task_json_info = requests.get(task_url).text
        task_dict_info = json.loads(task_json_info)
        tasks_list = task_dict_info.items()
    except:
        tasks_list = []

    result = []
    if (len(tasks_list) > 0):
        for key, value in tasks_list:
            if value["state"] == "STARTED":
                received_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["received"])) if value[
                    "received"] else ""

                result.append({
                    "uuid": value["uuid"],
                    "args": value["args"][1:-1],
                    "received": received_time,
                    "state": "执行中",
                })
    # # 根据字典中的值对字典进行排序
    # result = sorted(result, key=itemgetter('received'), reverse=True)
    return JsonResponse({"data": result})


def set_error_state(temp_request, process_run_id, task_content):
    current_process_runs = ProcessRun.objects.filter(id=process_run_id)
    if current_process_runs:
        current_process_run = current_process_runs[0]
        current_process_run.state = "ERROR"
        current_process_run.save()
        current_step_runs = current_process_run.steprun_set.filter(state="RUN")
        if len(current_step_runs) > 1:
            for current_step_run in current_step_runs:
                if current_step_run.step.pnode_id is not None:
                    current_step_run.state = "ERROR"
                    current_step_run.save()
                    current_script_runs = current_step_run.scriptrun_set.filter(state="RUN")
                    if current_script_runs:
                        current_script_run = current_script_runs[0]
                        current_script_run.state = "ERROR"
                        current_script_run.explain = task_content
                        current_script_run.save()
        myprocesstask = ProcessTask()
        myprocesstask.processrun_id = process_run_id
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = temp_request.user.username
        myprocesstask.type = "INFO"
        myprocesstask.logtype = "ERROR"
        myprocesstask.state = "1"
        myprocesstask.content = task_content
        myprocesstask.save()
    else:
        raise Http404()


@login_required
def revoke_current_task(request):
    process_run_id = request.POST.get("process_run_id", "")
    abnormal = request.POST.get("abnormal", "")
    task_url = "http://127.0.0.1:5555/api/tasks"

    try:
        process_run_id = int(process_run_id)
    except:
        return JsonResponse({"data": "流程不存在。"})

    try:
        task_json_info = requests.get(task_url).text
    except:
        return JsonResponse({"data": "终端未启动flower异步任务监控！"})

    task_dict_info = json.loads(task_json_info)
    task_id = ""

    for key, value in task_dict_info.items():
        try:
            task_process_id = int(value["args"][1:-1])
        except:
            task_process_id = ""
        # 终止指定流程的异步任务
        if value["state"] in ["STARTED", "SUCCESS"] and task_process_id == process_run_id:
            task_id = key
            break

    # abnormal 对异步任务进行的类型判断
    #   1.手动终止异步任务
    #   2.手动终止异步任务，但不修改流程状态
    #   0.被动终止异步任务：celery-flower检测不到异步任务，但是流程还在跑

    if abnormal in ["1", "2"]:
        stop_url = "http://127.0.0.1:5555/api/task/revoke/{0}?terminate=true".format(task_id)
        response = requests.post(stop_url)
        task_content = "异步任务被自主关闭。"

        # 终止任务
        if task_id:
            # "1"修改状态  "2"表示强制终止流程时终止异步任务，不改变STOP状态为ERROR
            if abnormal == "1":
                # 修改当前步骤/脚本/流程的状态为ERROR
                set_error_state(request, process_run_id, task_content)
            return JsonResponse({"data": task_content})

        else:
            return JsonResponse({"data": "当前任务不存在"})

    else:
        task_content = "异步任务异常关闭。"

        # 终止任务
        if not task_id:
            # 修改当前步骤/脚本/流程的状态为ERROR
            set_error_state(request, process_run_id, task_content)

            return JsonResponse({"data": task_content})
        else:
            return JsonResponse({"data": "异步任务未出现异常"})


@login_required
def get_script_log(request):
    script_run_id = request.POST.get("scriptRunId", "")
    try:
        script_run_id = int(script_run_id)
    except:
        raise Http404()

    current_script_run = ScriptRun.objects.filter(id=script_run_id).select_related("script")
    log_info = ""
    if current_script_run:
        current_script_run = current_script_run[0]
        log_address = current_script_run.script.log_address

        # HostsManage
        cur_host_manage = current_script_run.script.hosts_manage
        remote_ip = cur_host_manage.host_ip
        remote_user = cur_host_manage.username
        remote_password = cur_host_manage.password
        script_type = cur_host_manage.type

        if script_type == "SSH":
            remote_platform = "Linux"
            remote_cmd = "cat {0}".format(log_address)
        else:
            remote_platform = "Windows"
            remote_cmd = "type {0}".format(log_address)
        server_obj = ServerByPara(r"{0}".format(remote_cmd), remote_ip, remote_user, remote_password,
                                  remote_platform)
        result = server_obj.run("")
        base_data = result["data"]

        if result["exec_tag"] == "1":
            res = 0
            data = "{0} 导致获取日志信息失败！".format(base_data)
        else:
            res = "1"
            data = base_data
    else:
        res = "0"
        data = "当前脚本不存在！"
    return JsonResponse({
        "res": res,
        "log_info": data,
    })


@login_required
def processsignsave(request):
    """
    判断是否最后一个签字，如果是,签字后启动程序
    :param request:
    :return:
    """
    if 'task_id' in request.POST:
        result = {}
        id = request.POST.get('task_id', '')
        sign_info = request.POST.get('sign_info', '')

        try:
            id = int(id)
        except:
            raise Http404()
        try:
            process_task = ProcessTask.objects.get(id=id)
            process_task.operator = request.user.username
            process_task.explain = sign_info
            process_task.endtime = datetime.datetime.now()
            process_task.state = "1"
            process_task.save()

            myprocessrun = process_task.processrun

            prosssigns = ProcessTask.objects.filter(processrun=myprocessrun, state="0")
            if len(prosssigns) <= 0:
                myprocessrun.state = "RUN"
                myprocessrun.starttime = datetime.datetime.now()
                myprocessrun.save()

                myprocess = myprocessrun.process
                myprocesstask = ProcessTask()
                myprocesstask.processrun = myprocessrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "START"
                myprocesstask.state = "1"
                myprocesstask.content = "流程启动。"
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = request.user.username
                myprocesstask.save()

                exec_process.delay(myprocessrun.id)
                result["res"] = "签字成功,同时启动流程。"
                result["data"] = "/processindex/" + str(myprocessrun.id)
            else:
                result["res"] = "签字成功。"
        except:
            result["res"] = "流程启动失败，请于管理员联系。"
        return JsonResponse(result)


@login_required
def save_task_remark(request):
    task_id = request.POST.get("task_id", "")
    sign_info_extra = request.POST.get("sign_info_extra", "")

    if task_id:
        c_process_task = ProcessTask.objects.filter(id=task_id)
        if c_process_task:
            c_process_task = c_process_task[0]
            c_process_task.explain = sign_info_extra
            c_process_task.save()
        return JsonResponse({"result": 1})
    else:
        return JsonResponse({"result": 0})


@login_required
def reload_task_nums(request):
    mygroup = []
    userinfo = request.user.userinfo
    guoups = userinfo.group.all()
    pop = False
    if len(guoups) > 0:
        for curguoup in guoups:
            mygroup.append(str(curguoup.id))
    allprosstasks = ProcessTask.objects.filter(
        Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(state="0").order_by(
        "-starttime").exclude(processrun__state="9").select_related("processrun", "processrun__process",
                                                                    "steprun__step", "steprun")
    total_task_info = {}
    message_task = []
    if len(allprosstasks) > 0:
        for task in allprosstasks:
            send_time = task.starttime
            process_name = task.processrun.process.name
            process_run_reason = task.processrun.run_reason
            task_id = task.id
            processrunid = task.processrun.id

            c_task_step_run = task.steprun
            if c_task_step_run:
                address = c_task_step_run.step.remark
                if not address:
                    address = ""
            else:
                address = ""

            task_nums = len(allprosstasks)
            process_color = task.processrun.process.color
            process_url = task.processrun.process.url + "/" + str(task.processrun.id)
            time = task.starttime

            # 图标与颜色
            if task.type == "ERROR":
                current_icon = "fa fa-exclamation-triangle"
                current_color = "label-danger"
            elif task.type == "SIGN":
                pop = True
                current_icon = "fa fa-user"
                current_color = "label-warning"
            elif task.type == "RUN":
                current_icon = "fa fa-bell-o"
                current_color = "label-warning"
            else:
                pass

            time = custom_time(time)

            message_task.append(
                {"content": task.content, "time": time, "process_name": process_name, "processrunid": processrunid,
                 "task_color": current_color.strip(), "task_type": task.type, "task_extra": task.content,
                 "task_icon": current_icon, "process_color": process_color.strip(), "process_url": process_url,
                 "pop": pop, "task_id": task_id, "send_time": send_time.strftime("%Y-%m-%d %H:%M:%S"),
                 "process_run_reason": process_run_reason, "group_name": guoups[0].name, "address": address})

    total_task_info["task_nums"] = len(allprosstasks)
    total_task_info["message_task"] = message_task

    return JsonResponse(total_task_info)


@login_required
def get_current_scriptinfo(request):
    current_step_id = request.POST.get('steprunid', '')
    selected_script_id = request.POST.get('scriptid', '')

    if selected_script_id:
        try:
            selected_script_id = int(selected_script_id)
        except:
            selected_script_id = None
    else:
        selected_script_id = None

    scriptrun_objs = ScriptRun.objects.filter(id=selected_script_id)
    script_id = scriptrun_objs[0].script_id if scriptrun_objs else None

    script_objs = Script.objects.filter(id=script_id)
    script_obj = script_objs[0] if script_objs else None

    if script_obj:
        scriptrun_obj = scriptrun_objs[0]
        step_id_from_script = scriptrun_obj.steprun.step_id
        show_button = ""
        if step_id_from_script == current_step_id:
            # 显示button
            show_button = 1
        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "": "",
        }

        starttime = scriptrun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S") if scriptrun_obj.starttime else ""
        endtime = scriptrun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S") if scriptrun_obj.endtime else ""

        target = ""
        if script_obj.interface_type == "commvault":
            if scriptrun_obj.steprun.processrun.target:
                target = scriptrun_obj.steprun.processrun.target.client_name

        script_info = {
            "processrunstate": scriptrun_obj.steprun.processrun.state,
            "code": script_obj.code,
            "ip": script_obj.hosts_manage.host_ip if script_obj.hosts_manage else "",
            "filename": script_obj.filename,
            "scriptpath": script_obj.scriptpath,
            "state": state_dict["{0}".format(scriptrun_obj.state)],
            "starttime": starttime,
            "endtime": endtime,
            "operator": scriptrun_obj.operator,
            "explain": scriptrun_obj.explain,
            "show_button": show_button,
            "step_id_from_script": step_id_from_script,
            "show_log_btn": "1" if script_obj.log_address else "0",
            "origin": script_obj.origin.client_name if script_obj.origin else "",
            "target": target,
            "interface_type": script_obj.interface_type,
        }

        return JsonResponse({"data": script_info})


@login_required
def ignore_current_script(request):
    selected_script_id = request.POST.get('scriptid', '')
    scriptruns = ScriptRun.objects.filter(id=selected_script_id)[0]
    scriptruns.state = "IGNORE"
    scriptruns.save()

    # 继续运行
    current_script_run = ScriptRun.objects.filter(id=selected_script_id)
    if current_script_run:
        current_script_run = current_script_run[0]
        current_process_run = current_script_run.steprun.processrun
        current_process_run_id = current_process_run.id
        exec_process.delay(current_process_run_id, if_repeat=True)

        return JsonResponse({"data": "成功忽略当前脚本！", "result": 1})
    else:
        return JsonResponse({"data": "脚本忽略失败，请联系客服！", "result": 0})


@login_required
def stop_current_process(request):
    process_run_id = request.POST.get('process_run_id', '')
    process_note = request.POST.get('process_note', '')

    try:
        process_run_id = int(process_run_id)
    except ValueError as e:
        return JsonResponse({"data": "当前选择终止的流程不存在。"})

    current_process_run = ProcessRun.objects.exclude(state="9").filter(id=process_run_id)
    if current_process_run:
        current_process_run = current_process_run[0]

        all_current_step_runs = current_process_run.steprun_set.filter(Q(state="RUN") | Q(state="CONFIRM")).exclude(
            state="9")
        if all_current_step_runs:
            for all_current_step_run in all_current_step_runs:
                all_current_step_run.state = "EDIT"
                all_current_step_run.save()
                all_scripts_from_current_step = all_current_step_run.scriptrun_set.filter(state="RUN").exclude(
                    state="9")
                if all_scripts_from_current_step:
                    for script in all_scripts_from_current_step:
                        script.state = "EDIT"
                        script.save()

        current_process_run.state = "STOP"
        current_process_run.endtime = datetime.datetime.now()
        current_process_run.note = process_note
        current_process_run.save()

        all_tasks_ever = current_process_run.processtask_set.filter(state="0")
        if all_tasks_ever:
            for task in all_tasks_ever:
                task.endtime = datetime.datetime.now()
                task.state = "1"
                task.save()

        myprocesstask = ProcessTask()
        myprocesstask.processrun_id = process_run_id
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = request.user.username
        myprocesstask.type = "INFO"
        myprocesstask.logtype = "STOP"
        myprocesstask.state = "1"
        myprocesstask.content = "流程被终止。"
        myprocesstask.save()

        ######################
        # 执行强制执行的脚本  #
        ######################
        force_exec_script.delay(process_run_id)
        if current_process_run.walkthrough is not None:
            if current_process_run.walkthrough != "DONE":
                next_process_run = current_process_run.walkthrough.processrun_set.filter(state="PLAN")
                if next_process_run:
                    next_process_run = next_process_run[0]
                    next_process_run.starttime = datetime.datetime.now()
                    next_process_run.state = "RUN"
                    next_process_run.walkthroughstate = "RUN"
                    next_process_run.DataSet_id = 89
                    next_process_run.save()

                    process = Process.objects.filter(id=next_process_run.process_id).exclude(state="9").exclude(
                        Q(type=None) | Q(type=""))

                    allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                        "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                    if process[0].sign == "1" and len(allgroup) > 0:  # 如果流程需要签字,发送签字tasks
                        # 将当前流程改成SIGN
                        c_process_run_id = next_process_run.id
                        c_process_run = ProcessRun.objects.filter(id=c_process_run_id)
                        if c_process_run:
                            c_process_run = c_process_run[0]
                            c_process_run.state = "SIGN"
                            c_process_run.walkthroughstate = "RUN"
                            c_process_run.save()
                        for group in allgroup:
                            try:
                                signgroup = Group.objects.get(id=int(group["group"]))
                                groupname = signgroup.name
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = next_process_run
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.senduser = request.user.username
                                myprocesstask.receiveauth = group["group"]
                                myprocesstask.type = "SIGN"
                                myprocesstask.state = "0"
                                myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                                myprocesstask.save()
                            except:
                                pass

                    else:
                        prosssigns = ProcessTask.objects.filter(processrun=next_process_run, state="0")
                        if len(prosssigns) <= 0:
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = next_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.type = "INFO"
                            myprocesstask.logtype = "START"
                            myprocesstask.state = "1"
                            myprocesstask.senduser = request.user.username
                            myprocesstask.content = "流程启动。"
                            myprocesstask.save()

                            exec_process.delay(next_process_run.id)

        return JsonResponse({"data": "流程已经被终止，将强制执行部分脚本。"})
    else:
        return JsonResponse({"data": "终止流程异常，请联系客服"})


@login_required
def get_force_script_info(request):
    ####################################################################
    # 获取所有包含强制执行步骤的脚本信息                                 #
    #   {"finish": 1, "script_name_list": [], "script_status_list": []}#
    ####################################################################
    process_run_id = request.POST.get("process", "")

    try:
        process_run_id = int(process_run_id)
    except ValueError as e:
        print("网络异常, {0}".format(e))
        return JsonResponse({
            "ret": 0,
            "data": "网络异常, {0}".format(e)
        })

    try:
        cur_process_run = ProcessRun.objects.get(id=process_run_id)
    except ProcessRun.DoesNotExist as e:
        print("当前流程不存在, {0}".format(e))
        return JsonResponse({
            "ret": 0,
            "data": "当前流程不存在, {0}".format(e)
        })
    else:
        finish = 1
        cur_process_id = cur_process_run.process.id
        script_name_list = []
        script_status_list = []
        all_step_runs = cur_process_run.steprun_set.exclude(step__state="9").filter(step__force_exec=1)
        for step_run in all_step_runs:
            cur_step_scripts = step_run.scriptrun_set.all()
            for cur_script in cur_step_scripts:
                script_name_list.append(cur_script.script.name)
                script_status_list.append(cur_script.state)
                if cur_script.state not in ["ERROR", "DONE"]:
                    finish = 0
        return JsonResponse({
            "ret": 1,
            "data": {
                "finish": finish,
                "script_name_list": script_name_list,
                "script_status_list": script_status_list,
                "switch_url": "/falconstorswitch/{0}".format(cur_process_id)
            }
        })


@login_required
def verify_items(request):
    verify_array = request.POST.get("verify_array", "")
    step_id = request.POST.get("step_id", "")
    try:
        verify_array = eval(verify_array)
    except:
        verify_array = []
    current_step_run = StepRun.objects.filter(id=step_id).exclude(state="9").select_related("processrun",
                                                                                            "step").all()
    if current_step_run:
        current_step_run = current_step_run[0]

        ###########################################
        # VerifyItemsRun中has_verified修改成已确认 #
        ###########################################
        all_verify_item_run = current_step_run.verifyitemsrun_set.exclude(state="9").filter(id__in=verify_array)
        if all_verify_item_run.exists():
            all_verify_item_run.update(has_verified="1")

        # CONFIRM修改成CONTINUE
        current_step_run.state = "CONTINUE"
        current_step_run.endtime = datetime.datetime.now()
        current_step_run.save()

        processrun = current_step_run.processrun
        processrun.state = 'CONTINUE'
        processrun.save()

        all_current__tasks = current_step_run.processrun.processtask_set.exclude(state="1")
        for task in all_current__tasks:
            task.endtime = datetime.datetime.now()
            task.state = "1"
            task.save()

        # 写入继续任务
        myprocesstask = ProcessTask()
        myprocesstask.processrun_id = current_step_run.processrun_id
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = current_step_run.processrun.creatuser
        myprocesstask.receiveauth = current_step_run.step.group
        myprocesstask.type = "RUN"
        myprocesstask.state = "0"
        task_content = "流程" + current_step_run.step.process.name + "待继续，请处理。"
        myprocesstask.content = task_content
        myprocesstask.save()

        # # 运行流程
        # current_process_run_id = current_step_run.processrun_id
        # exec_process.delay(current_process_run_id, if_repeat=True)

        return JsonResponse({"data": "0"})
    else:
        return JsonResponse({"data": "1"})


@login_required
def processcontinue(request):
    step_id = ""
    if 'step_id' in request.POST:
        step_id = request.POST.get("step_id", "")
    else:
        processrun_id = request.POST.get("processrun_id", "")
        stepruns = StepRun.objects.filter(processrun_id=int(processrun_id), state='CONTINUE').exclude(state='9')
        if len(stepruns) > 0:
            step_id = stepruns[0].id
        else:
            return JsonResponse({"data": "1"})
    current_step_run = StepRun.objects.filter(id=step_id).exclude(state="9").select_related("processrun",
                                                                                            "step").all()
    if current_step_run:
        current_step_run = current_step_run[0]
        # CONFIRM修改成DONE
        current_step_run.state = "DONE"
        current_step_run.endtime = datetime.datetime.now()
        current_step_run.save()

        processrun = current_step_run.processrun
        processrun.state = 'RUN'
        processrun.save()

        all_current__tasks = current_step_run.processrun.processtask_set.exclude(state="1")
        for task in all_current__tasks:
            task.endtime = datetime.datetime.now()
            task.state = "1"
            task.save()

        # 写入任务
        myprocesstask = ProcessTask()
        myprocesstask.processrun_id = current_step_run.processrun_id
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = current_step_run.processrun.creatuser
        myprocesstask.type = "INFO"
        myprocesstask.logtype = "STEP"
        myprocesstask.state = "1"
        myprocesstask.content = "步骤" + current_step_run.step.name + "完成。"
        myprocesstask.save()

        # 运行流程
        current_process_run_id = current_step_run.processrun_id
        exec_process.delay(current_process_run_id, if_repeat=True)

        return JsonResponse({"data": "0"})
    else:
        return JsonResponse({"data": "1"})


@login_required
def show_result(request):
    processrun_id = request.POST.get("process_run_id", "")

    show_result_dict = {}

    try:
        processrun_id = int(processrun_id)
    except:
        raise Http404()

    current_processrun = ProcessRun.objects.filter(id=processrun_id)
    if current_processrun:
        current_processrun = current_processrun[0]
        process_id = current_processrun.process.id
    else:
        raise Http404()

    process_name = current_processrun.process.name if current_processrun else ""
    processrun_time = current_processrun.starttime.strftime("%Y-%m-%d")

    # 父级
    step_info_list = []
    pnode_steplist = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
        pnode_id=None)

    for num, pstep in enumerate(pnode_steplist):
        second_el_dict = dict()
        step_name = pstep.name
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
                second_el_dict["start_time"] = pnode_steprun.starttime.strftime(
                    "%Y-%m-%d %H:%M:%S") if pnode_steprun.starttime else ""
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
            if users:
                operator = users[0].userinfo.fullname
                second_el_dict["operator"] = operator
            else:
                second_el_dict["operator"] = ""
        except:
            second_el_dict["operator"] = ""

        p_id = pstep.id
        inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
            pnode_id=p_id)

        # 子级
        inner_step_list = []
        if inner_steps:
            for num, step in enumerate(inner_steps):
                inner_second_el_dict = dict()
                step_name = step.name
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
                        inner_second_el_dict["end_time"] = steprun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S") if \
                            steprun_obj.endtime else ""

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

                inner_step_list.append(inner_second_el_dict)
        second_el_dict['inner_step_list'] = inner_step_list
        step_info_list.append(second_el_dict)

    show_result_dict["step_info_list"] = step_info_list
    # 用户组信息
    all_groups = Group.objects.exclude(state="9")
    total_list = []
    if all_groups:
        for group in all_groups:
            all_group_dict = {}
            current_group_users = group.userinfo_set.exclude(state="9", pnode=None).filter(type="user")
            if current_group_users:
                all_group_dict["group"] = group.name

                current_users_and_departments = []
                for user in current_group_users:
                    inner_dict = {}
                    inner_dict["fullname"] = user.fullname
                    inner_dict["depart_name"] = user.pnode.fullname if user.pnode else ""
                    current_users_and_departments.append(inner_dict)
                all_group_dict["current_users_and_departments"] = current_users_and_departments
                total_list.append(all_group_dict)
    show_result_dict["total_list"] = total_list

    # process_name
    show_result_dict["process_name"] = process_name
    # processrun_time
    show_result_dict["processrun_time"] = processrun_time

    # 项目起始时间，结束时间，RTO
    show_result_dict["start_time"] = current_processrun.starttime.strftime(
        "%Y-%m-%d %H:%M:%S") if current_processrun.starttime else ""
    show_result_dict["end_time"] = current_processrun.endtime.strftime(
        "%Y-%m-%d %H:%M:%S") if current_processrun.endtime else ""

    all_step_runs = current_processrun.steprun_set.exclude(state="9").exclude(step__rto_count_in="0").filter(
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
    all_inner_step_runs = current_processrun.steprun_set.exclude(state="9").filter(
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
    show_result_dict["rto"] = "%d时%02d分%02d秒" % (h, m, s)

    return JsonResponse(show_result_dict)


@login_required
def reject_invited(request):
    plan_process_run_id = request.POST.get("plan_process_run_id", "")
    rejected_process_runs = ProcessRun.objects.filter(id=plan_process_run_id)
    if rejected_process_runs:
        rejected_process_run = rejected_process_runs[0]
        rejected_process_run.state = "REJECT"
        rejected_process_run.save()

        # 生成取消任务信息
        myprocesstask = ProcessTask()
        myprocesstask.processrun_id = rejected_process_run.id
        myprocesstask.starttime = datetime.datetime.now()
        myprocesstask.senduser = request.user.username
        myprocesstask.type = "INFO"
        myprocesstask.logtype = "REJECT"
        myprocesstask.state = "1"
        myprocesstask.content = "取消演练计划。"
        myprocesstask.save()

        result = "取消演练计划成功！"
    else:
        result = "计划流程不存在，取消失败！"
    return JsonResponse({"res": result})


@login_required
def delete_current_process_run(request):
    processrun_id = request.POST.get("processrun_id", "")

    try:
        processrun_id = int(processrun_id)
    except:
        raise Http404()

    current_process_run = ProcessRun.objects.filter(id=processrun_id)
    if current_process_run:
        current_process_run = current_process_run[0]
        current_process_run.state = "9"
        current_process_run.save()
        return HttpResponse(1)
    else:
        return HttpResponse(0)


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

        current_scripts = Script.objects.exclude(state="9").filter(step_id=pstep.id).order_by("sort")
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
                    current_scripts = Script.objects.exclude(state="9").filter(step_id=step.id).order_by("sort")

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
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")).order_by('-id')
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
    return render(request, "falconstorsearch.html",
                  {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                   "processname_list": processname_list, "state_dict": state_dict,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def falconstorsearchdata(request):
    """
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

    cursor = connection.cursor()

    exec_sql = """
    select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
    left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.starttime between '{0}' and '{1}' order by r.starttime desc;
    """.format(start_time, end_time)

    if runperson:
        user_info = UserInfo.objects.filter(fullname=runperson)
        if user_info:
            user_info = user_info[0]
            runperson = user_info.user.username
        else:
            runperson = ""

        if processname != "" and runstate != "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.state='{1}' and r.creatuser='{2}' and r.starttime between '{3}' and '{4}'  order by r.starttime desc;
            """.format(processname, runstate, runperson, start_time, end_time)

        if processname == "" and runstate != "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.state='{0}' and r.creatuser='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
            """.format(runstate, runperson, start_time, end_time)

        if processname != "" and runstate == "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.creatuser='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
            """.format(processname, runperson, start_time, end_time)
        if processname == "" and runstate == "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.creatuser='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
            """.format(runperson, start_time, end_time)

    else:
        if processname != "" and runstate != "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.state='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
            """.format(processname, runstate, start_time, end_time)

        if processname == "" and runstate != "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.state='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
            """.format(runstate, start_time, end_time)

        if processname != "" and runstate == "":
            exec_sql = """
            select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
            left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
            """.format(processname, start_time, end_time)

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
    cursor.execute(exec_sql)
    rows = cursor.fetchall()

    for processrun_obj in rows:
        create_users = processrun_obj[2] if processrun_obj[2] else ""
        create_user_objs = User.objects.filter(username=create_users)
        create_user_fullname = create_user_objs[0].userinfo.fullname if create_user_objs else ""

        result.append({
            "starttime": processrun_obj[0].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[0] else "",
            "endtime": processrun_obj[1].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[1] else "",
            "createuser": create_user_fullname,
            "state": state_dict["{0}".format(processrun_obj[3])] if processrun_obj[3] else "",
            "process_id": processrun_obj[4] if processrun_obj[4] else "",
            "processrun_id": processrun_obj[5] if processrun_obj[5] else "",
            "run_reason": processrun_obj[6][:20] if processrun_obj[6] else "",
            "process_name": processrun_obj[7] if processrun_obj[7] else "",
            "process_url": processrun_obj[8] if processrun_obj[8] else ""
        })
    return HttpResponse(json.dumps({"data": result}))


@login_required
def tasksearch(request, funid):
    nowtime = datetime.datetime.now()
    endtime = nowtime.strftime("%Y-%m-%d")
    starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))
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

    cursor = connection.cursor()
    exec_sql = """
    select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
    left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type!='INFO' and r.state!='9' and t.starttime between '{0}' and '{1}' order by t.starttime desc;
    """.format(start_time, end_time)

    if task_type != "" and has_finished != "":
        exec_sql = """
        select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
        left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type='{0}' and r.state!='9' and t.state='{1}' and t.starttime between '{2}' and '{3}' order by t.starttime desc;
        """.format(task_type, has_finished, start_time, end_time)

    if task_type == "" and has_finished != "":
        exec_sql = """
        select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
        left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where  t.type!='INFO' and r.state!='9' and t.state='{0}' and t.starttime between '{1}' and '{2}' order by t.starttime desc;
        """.format(has_finished, start_time, end_time)

    if task_type != "" and has_finished == "":
        exec_sql = """
        select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
        left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type='{0}' and r.state!='9' and t.starttime between '{1}' and '{2}' order by t.starttime desc;
        """.format(task_type, start_time, end_time)

    cursor.execute(exec_sql)
    rows = cursor.fetchall()
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
            "task_id": task[0],
            "task_content": task[1],
            "starttime": task[2].strftime('%Y-%m-%d %H:%M:%S') if task[2] else "",
            "endtime": task[3].strftime('%Y-%m-%d %H:%M:%S') if task[3] else "",
            "type": type_dict["{0}".format(task[4])] if task[4] in type_dict.keys() else "",
            "processrun_id": task[5] if task[5] else "",
            "process_name": task[6] if task[6] else "",
            "process_url": task[7] if task[7] else "",
            "has_finished": has_finished_dict[
                "{0}".format(task[8])] if task[8] in has_finished_dict.keys() else "",
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


@login_required
def save_invitation(request):
    result = {}
    process_id = request.POST.get("process_id", "")
    start_time = request.POST.get("start_time", "")
    purpose = request.POST.get("purpose", "")
    end_time = request.POST.get("end_time", "")

    # 准备流程PLAN
    try:
        process_id = int(process_id)
    except:
        raise Http404()

    if start_time:
        if end_time:
            process = Process.objects.filter(id=process_id).exclude(state="9").exclude(Q(type=None) | Q(type=""))
            if (len(process) <= 0):
                result["res"] = '流程计划失败，该流程不存在。'
            else:

                planning_process = ProcessRun.objects.filter(process=process[0], state="PLAN")
                if (len(planning_process) > 0):
                    result["res"] = '流程计划失败，已经存在计划流程，务必先完成该计划流程。'
                else:
                    curprocessrun = ProcessRun.objects.filter(process=process[0], state__in=["RUN", "ERROR"])
                    if (len(curprocessrun) > 0):
                        result["res"] = '流程计划失败，有流程正在进行中，请勿重复启动。'
                    else:
                        myprocessrun = ProcessRun()
                        myprocessrun.process = process[0]
                        myprocessrun.state = "PLAN"
                        myprocessrun.starttime = datetime.datetime.now()
                        myprocessrun.save()
                        current_process_run_id = myprocessrun.id

                        process = Process.objects.filter(id=process_id).exclude(state="9").exclude(
                            Q(type="") & Q(type=None))
                        mystep = process[0].step_set.exclude(state="9")
                        if (len(mystep) <= 0):
                            result["res"] = '流程启动失败，没有找到可用步骤。'
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

                                myverifyitems = step.verifyitems_set.exclude(state="9")
                                for verifyitems in myverifyitems:
                                    myverifyitemsrun = VerifyItemsRun()
                                    myverifyitemsrun.verify_items = verifyitems
                                    myverifyitemsrun.steprun = mysteprun
                                    myverifyitemsrun.save()

                        # 保存邀请函
                        current_invitation = Invitation()
                        current_invitation.process_run_id = current_process_run_id
                        current_invitation.start_time = start_time
                        current_invitation.end_time = end_time
                        current_invitation.purpose = purpose
                        current_invitation.current_time = datetime.datetime.now()
                        current_invitation.save()

                        # 生成邀请任务信息
                        myprocesstask = ProcessTask()
                        myprocesstask.processrun_id = current_process_run_id
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = request.user.username
                        myprocesstask.type = "INFO"
                        myprocesstask.logtype = "PLAN"
                        myprocesstask.state = "1"
                        myprocesstask.content = "创建流程计划。"
                        myprocesstask.save()

                        result["data"] = current_process_run_id
                        result["res"] = "流程计划成功，待开启流程。"
        else:
            result["res"] = "演练结束时间必须填写！"
    else:
        result["res"] = "演练开始时间必须填写！"

    return JsonResponse(result)


@login_required
def save_modify_invitation(request):
    result = {}
    plan_process_run_id = request.POST.get("plan_process_run_id", "")
    start_time = request.POST.get("start_date_modify", "")
    purpose = request.POST.get("purpose_modify", "")
    end_time = request.POST.get("end_date_modify", "")

    try:
        plan_process_run_id = int(plan_process_run_id)
    except:
        raise Http404()

    if start_time:
        if end_time:
            current_invitation = Invitation.objects.filter(process_run_id=plan_process_run_id)
            if current_invitation:
                current_invitation = current_invitation[0]

                current_invitation.start_time = start_time
                current_invitation.end_time = end_time
                current_invitation.purpose = purpose
                current_invitation.save()

                # 生成邀请任务信息
                myprocesstask = ProcessTask()
                myprocesstask.processrun_id = plan_process_run_id
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = request.user.username
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "PLAN"
                myprocesstask.state = "1"
                myprocesstask.content = "修改演练计划。"
                myprocesstask.save()

                result["data"] = plan_process_run_id
                result["res"] = "修改流程计划成功，待开启流程。"
            else:
                result["res"] = "演练计划不存在，请联系客服！"
        else:
            result["res"] = "演练结束时间必须填写！"
    else:
        result["res"] = "演练开始时间必须填写！"

    return JsonResponse(result)


@login_required
def fill_with_invitation(request):
    plan_process_run_id = request.POST.get("plan_process_run_id", "")
    current_invitation = Invitation.objects.filter(process_run_id=plan_process_run_id)
    if current_invitation:
        current_invitation = current_invitation[0]
        start_time = current_invitation.start_time
        end_time = current_invitation.end_time
        purpose = current_invitation.purpose
        return JsonResponse({
            "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else "",
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else "",
            "purpose": purpose,
        })


@login_required
def invite(request):
    walkthrough_id = request.GET.get("walkthrough_id", "")
    start_date = request.GET.get("start_date", "")
    purpose = request.GET.get("purpose", "")
    end_date = request.GET.get("end_date", "")
    process_date = start_date
    nowtime = datetime.datetime.now()
    invite_time = nowtime.strftime("%Y-%m-%d")

    try:
        walkthrough_id = int(walkthrough_id)
    except ValueError as e:
        raise Http404()

    try:
        cur_walkthrough = Walkthrough.objects.get(id=walkthrough_id)
    except Walkthrough.DoesNotExist as e:
        raise Http404()
    else:
        current_process_runs = cur_walkthrough.processrun_set.exclude(state="9")
        process_name_list = []
        pre_process_name = ""
        all_group_list = []

        for process_run in current_process_runs:
            if pre_process_name == process_run.process.name:
                continue
            process_name_list.append(process_run.process.name)
            pre_process_name = process_run.process.name

            allgroup = process_run.process.step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                "group").distinct()

            if allgroup:
                for num, current_group in enumerate(allgroup):
                    try:
                        group = Group.objects.get(id=int(current_group["group"]))
                    except Group.DoesNotExist as e:
                        pass
                    else:
                        if group.name not in all_group_list:
                            all_group_list.append(group.name)
        all_groups = ""

        for num, group in enumerate(all_group_list):
            if num == len(all_group_list) - 1:
                all_groups += group
            else:
                all_groups += group + "、"

        whole_process_name = ""

        for num, process_name in enumerate(process_name_list):
            if num == len(process_name_list) - 1:
                whole_process_name += process_name
            else:
                whole_process_name += process_name + "、"

        t = TemplateResponse(request, 'notice.html',
                             {"process_date": process_date, "purpose": purpose, "invite_time": invite_time,
                              "start_date": start_date,
                              "end_date": end_date, "whole_process_name": whole_process_name,
                              "all_groups": all_groups})
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
        css_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "new" + os.sep + "css"
        css_01 = css_path + os.sep + "bootstrap.css"
        # css_02 = css_path + os.sep + "font-awesome.min.css"
        css_03 = css_path + os.sep + "icon.css"
        # css_04 = css_path + os.sep + "font.css"
        css_05 = css_path + os.sep + "app.css"
        css_06 = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "assets" + os.sep + "global" + os.sep + "css" + os.sep + "components.css"

        css = [r"{0}".format(mycss) for mycss in [css_01, css_03, css_05, css_06]]

        pdfkit.from_string(t.content.decode(encoding="utf-8"), r"invitation.pdf", configuration=config,
                           options=options,
                           css=css)

        the_file_name = "invitation.pdf"
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
        return response


@login_required
def get_all_users(request):
    all_users = UserInfo.objects.exclude(user=None)
    user_string = ""
    for user in all_users:
        user_string += user.fullname + "&"
    return JsonResponse({"data": user_string})


def get_contact_org_tree(parent, selectid):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9").all()
    for child in children:
        if child.type == "org":
            node = {}
            node["text"] = child.fullname
            node["id"] = child.id
            node["type"] = child.type

            node["children"] = get_contact_org_tree(child, selectid)
            try:
                if int(selectid) == child.id:
                    node["state"] = {"selected": True}
            except:
                pass
            nodes.append(node)
    return nodes


@login_required
def contact(request, funid):
    return render(request, 'contact.html',
                  {'username': request.user.userinfo.fullname,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def get_contact_tree(request):
    selectid = ""
    treedata = []
    rootnodes = UserInfo.objects.order_by("sort").exclude(state="9").filter(pnode=None, type="org")
    if len(rootnodes) > 0:
        for rootnode in rootnodes:
            root = {}
            root["text"] = rootnode.fullname
            root["id"] = rootnode.id
            root["type"] = "org"

            root["data"] = {"remark": rootnode.remark, "pname": "无"}
            try:
                if int(selectid) == rootnode.id:
                    root["state"] = {"opened": True, "selected": True}
                else:
                    root["state"] = {"opened": True}
            except:
                root["state"] = {"opened": True}
            root["children"] = get_contact_org_tree(rootnode, selectid)
            treedata.append(root)
    return JsonResponse({"data": treedata})


def get_child_contact(cur_contact_id, contact_list):
    child_contacts = UserInfo.objects.filter(pnode_id=cur_contact_id).exclude(state="9")

    for cur_contact in child_contacts:
        if cur_contact.type == "user":
            try:
                parent_contact_org = UserInfo.objects.get(id=cur_contact.id)
            except:
                pass
            else:
                if parent_contact_org.pnode:
                    depart = parent_contact_org.pnode.fullname
                else:
                    depart = ""

                contact_list.append({
                    "user_name": cur_contact.fullname,
                    "tel": cur_contact.phone,
                    "email": cur_contact.user.email,
                    "depart": depart,
                })
        else:
            get_child_contact(cur_contact.id, contact_list)


@login_required
def get_contact_info(request):
    user_id = request.GET.get("user_id", "")

    try:
        user_id = int(user_id)
    except:
        JsonResponse({"data": []})

    contact_list = []
    # 查看当前节点下所有userinfo的type为user的信息
    if user_id == 0:
        # pnode不为空，state不为"9"，type为"user"
        all_contacts = UserInfo.objects.exclude(state="9").filter(type="user")
        for contact in all_contacts:
            if contact.pnode_id != None:
                try:
                    parent_contact_org = UserInfo.objects.get(id=contact.id)
                except:
                    pass
                else:
                    if parent_contact_org.pnode:
                        depart = parent_contact_org.pnode.fullname
                    else:
                        depart = ""

                    contact_list.append({
                        "user_name": contact.fullname,
                        "tel": contact.phone,
                        "email": contact.user.email,
                        "depart": depart,
                    })
    else:
        # 当前节点下所有用户信息
        get_child_contact(user_id, contact_list)

    return JsonResponse({"data": contact_list})


@login_required
def hosts_manage(request, funid):
    return render(request, 'hosts_manage.html',
                  {'username': request.user.userinfo.fullname,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def host_save(request):
    host_id = request.POST.get("host_id", "")
    host_ip = request.POST.get("host_ip", "")
    host_name = request.POST.get("host_name", "")
    host_os = request.POST.get("os", "")
    connect_type = request.POST.get("type", "")
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    config = request.POST.get("config", "")

    ret = 0
    info = ""
    try:
        host_id = int(host_id)
    except:
        ret = 0
        info = "网络错误。"
    else:
        if host_ip.strip():
            if host_name.strip():
                if host_os.strip():
                    if connect_type.strip():
                        if username.strip():
                            if password.strip():
                                # 主机参数
                                root = etree.Element("root")

                                if config:
                                    config = json.loads(config)
                                    # 动态参数
                                    for c_config in config:
                                        param_node = etree.SubElement(root, "param")
                                        param_node.attrib["param_name"] = c_config["param_name"].strip()
                                        param_node.attrib["variable_name"] = c_config["variable_name"].strip()
                                        param_node.attrib["param_value"] = c_config["param_value"].strip()
                                config = etree.tounicode(root)

                                # 新增
                                if host_id == 0:
                                    # 判断主机是否已经存在
                                    check_host_manage = HostsManage.objects.filter(host_ip=host_ip)
                                    if check_host_manage.exists():
                                        ret = 0
                                        info = "主机已经存在，请勿重复添加。"
                                    else:
                                        try:
                                            cur_host_manage = HostsManage()
                                            cur_host_manage.host_ip = host_ip
                                            cur_host_manage.host_name = host_name
                                            cur_host_manage.os = host_os
                                            cur_host_manage.type = connect_type
                                            cur_host_manage.username = username
                                            cur_host_manage.password = password
                                            cur_host_manage.config = config
                                            cur_host_manage.save()
                                        except:
                                            ret = 0
                                            info = "服务器异常。"
                                        else:
                                            ret = 1
                                            info = "新增主机成功。"
                                else:
                                    # 修改
                                    try:
                                        cur_host_manage = HostsManage.objects.get(id=host_id)
                                        cur_host_manage.host_ip = host_ip
                                        cur_host_manage.host_name = host_name
                                        cur_host_manage.os = host_os
                                        cur_host_manage.type = connect_type
                                        cur_host_manage.username = username
                                        cur_host_manage.password = password
                                        cur_host_manage.config = config
                                        cur_host_manage.save()

                                        ret = 1
                                        info = "主机信息修改成功。"
                                    except:
                                        ret = 0
                                        info = "服务器异常。"
                            else:
                                ret = 0
                                info = "密码未填写。"
                        else:
                            ret = 0
                            info = "用户名未填写。"
                    else:
                        ret = 0
                        info = "连接类型未选择。"
                else:
                    ret = 0
                    info = "系统未选择。"
            else:
                ret = 0
                info = "主机名称不能为空。"
        else:
            ret = 0
            info = "主机IP未填写。"
        return JsonResponse({
            "ret": ret,
            "info": info
        })


@login_required
def hosts_manage_data(request):
    all_hosts_manage = HostsManage.objects.exclude(state="9")
    all_hm_list = []
    for host_manage in all_hosts_manage:
        param_list = []
        try:
            config = etree.XML(host_manage.config)

            param_el = config.xpath("//param")
            for v_param in param_el:
                param_list.append({
                    "param_name": v_param.attrib.get("param_name", ""),
                    "variable_name": v_param.attrib.get("variable_name", ""),
                    "param_value": v_param.attrib.get("param_value", ""),
                })
        except Exception as e:
            print(e)
        all_hm_list.append({
            "host_id": host_manage.id,
            "host_ip": host_manage.host_ip,
            "host_name": host_manage.host_name,
            "os": host_manage.os,
            "type": host_manage.type,
            "username": host_manage.username,
            "password": host_manage.password,
            "variable_param_list": param_list,
        })
    return JsonResponse({"data": all_hm_list})


@login_required
def hosts_manage_del(request):
    host_id = request.POST.get("host_id", "")

    try:
        cur_host_manage = HostsManage.objects.get(id=int(host_id))
    except:
        return JsonResponse({
            "ret": 0,
            "info": "当前网络异常"
        })
    else:
        try:
            cur_host_manage.state = "9"
            cur_host_manage.save()
        except:
            return JsonResponse({
                "ret": 0,
                "info": "服务器网络异常。"
            })
        else:
            return JsonResponse({
                "ret": 1,
                "info": "删除成功。"
            })


######################
# 工具管理
######################
@login_required
def util_manage(request, funid):
    return render(request, 'util_manage.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})


def get_credit_info(content):
    commvault_credit = {
        'webaddr': '',
        'port': '',
        'hostusername': '',
        'hostpasswd': '',
        'username': '',
        'passwd': '',
    }
    sqlserver_credit = {
        'SQLServerHost': '',
        'SQLServerUser': '',
        'SQLServerPasswd': '',
        'SQLServerDataBase': '',
    }
    try:
        doc = etree.XML(content)

        # Commvault账户信息
        try:
            commvault_credit['webaddr'] = doc.xpath('//webaddr/text()')[0]
        except:
            pass
        try:
            commvault_credit['port'] = doc.xpath('//port/text()')[0]
        except:
            pass
        try:
            commvault_credit['hostusername'] = doc.xpath('//hostusername/text()')[0]
        except:
            pass
        try:
            commvault_credit['hostpasswd'] = base64.b64decode(doc.xpath('//hostpasswd/text()')[0]).decode()
        except:
            pass
        try:
            commvault_credit['username'] = doc.xpath('//username/text()')[0]
        except:
            pass
        try:
            commvault_credit['passwd'] = base64.b64decode(doc.xpath('//passwd/text()')[0]).decode()
        except:
            pass

        # SQL Server账户信息
        try:
            sqlserver_credit['SQLServerHost'] = doc.xpath('//SQLServerHost/text()')[0]
        except:
            pass
        try:
            sqlserver_credit['SQLServerUser'] = doc.xpath('//SQLServerUser/text()')[0]
        except:
            pass
        try:
            sqlserver_credit['SQLServerPasswd'] = base64.b64decode(
                doc.xpath('//SQLServerPasswd/text()')[0]).decode()
        except:
            pass
        try:
            sqlserver_credit['SQLServerDataBase'] = doc.xpath('//SQLServerDataBase/text()')[0]
        except:
            pass

    except Exception as e:
        print(e)
    return commvault_credit, sqlserver_credit


@login_required
def util_manage_data(request):
    """
    工具管理信息
    """
    util_manage_list = []

    util_manages = UtilsManage.objects.exclude(state='9')

    for um in util_manages:
        commvault_credit = {
            'webaddr': '',
            'port': '',
            'hostusername': '',
            'hostpasswd': '',
            'username': '',
            'passwd': '',
        }
        sqlserver_credit = {
            'SQLServerHost': '',
            'SQLServerUser': '',
            'SQLServerPasswd': '',
            'SQLServerDataBase': '',
        }
        if um.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(um.content)

        util_manage_list.append({
            'id': um.id,
            'code': um.code,
            'name': um.name,
            'util_type': um.util_type,
            'commvault_credit': commvault_credit,
            'sqlserver_credit': sqlserver_credit
        })

    return JsonResponse({"data": util_manage_list})


@login_required
def util_manage_save(request):
    status = 1
    info = '保存成功。'

    util_manage_id = request.POST.get('util_manage_id', '')

    util_type = request.POST.get('util_type', '')
    code = request.POST.get('code', '')
    name = request.POST.get('name', '')

    webaddr = request.POST.get('webaddr', '')
    port = request.POST.get('port', '')
    hostusername = request.POST.get('hostusernm', '')
    hostpasswd = request.POST.get('hostpasswd', '')
    username = request.POST.get('usernm', '')
    passwd = request.POST.get('passwd', '')

    SQLServerHost = request.POST.get('SQLServerHost', '')
    SQLServerUser = request.POST.get('SQLServerUser', '')
    SQLServerPasswd = request.POST.get('SQLServerPasswd', '')
    SQLServerDataBase = request.POST.get('SQLServerDataBase', '')

    credit = ''

    try:
        util_manage_id = int(util_manage_id)
    except:
        status = 0
        info = '网络异常。'
    else:
        if not util_type.strip():
            status = 0
            info = '工具类型未选择。'
        elif not code.strip():
            status = 0
            info = '工具编号未填写。'
        elif not name.strip():
            status = 0
            info = '工具名称未填写。'
        elif UtilsManage.objects.exclude(state='9').exclude(id=util_manage_id).filter(code=code).exists():
            status = 0
            info = '工具编号已存在。'
        else:
            if util_type.strip().upper() == 'COMMVAULT':
                credit = """<?xml version="1.0" ?>
                    <vendor>
                        <webaddr>{webaddr}</webaddr>
                        <port>{port}</port>
                        <hostusername>{hostusername}</hostusername>
                        <hostpasswd>{hostpasswd}</hostpasswd>
                        <username>{username}</username>
                        <passwd>{passwd}</passwd>
                        <SQLServerHost>{SQLServerHost}</SQLServerHost>
                        <SQLServerUser>{SQLServerUser}</SQLServerUser>
                        <SQLServerPasswd>{SQLServerPasswd}</SQLServerPasswd>
                        <SQLServerDataBase>{SQLServerDataBase}</SQLServerDataBase>
                    </vendor>""".format(**{
                    "webaddr": webaddr,
                    "port": port,
                    "hostusername": hostusername,
                    "hostpasswd": base64.b64encode(hostpasswd.encode()).decode(),
                    "username": username,
                    "passwd": base64.b64encode(passwd.encode()).decode(),
                    "SQLServerHost": SQLServerHost,
                    "SQLServerUser": SQLServerUser,
                    "SQLServerPasswd": base64.b64encode(SQLServerPasswd.encode()).decode(),
                    "SQLServerDataBase": SQLServerDataBase
                })
            try:
                cur_util_manage = UtilsManage.objects.filter(id=util_manage_id)
                if cur_util_manage.exists():
                    cur_util_manage.update(**{
                        'util_type': util_type,
                        'code': code,
                        'name': name,
                        'content': credit
                    })
                else:
                    cur_util_manage.create(**{
                        'util_type': util_type,
                        'code': code,
                        'name': name,
                        'content': credit
                    })
            except Exception as e:
                print(e)
                status = 0
                info = '保存失败。'

    return JsonResponse({
        'status': status,
        'info': info,
    })


@login_required
def util_manage_del(request):
    status = 1
    info = '删除成功。'
    util_manage_id = request.POST.get('util_manage_id', '')

    try:
        util_manage_id = int(util_manage_id)
    except:
        status = 0
        info = '网络异常。'
    else:
        util_manage = UtilsManage.objects.filter(id=util_manage_id)
        if util_manage.exists():
            util_manage.update(**{'state': '9'})
        else:
            status = 0
            info = '该工具不存在，删除失败。'
    return JsonResponse({
        'status': status,
        'info': info
    })


def get_oracle_client(um):
    # 解析出账户信息
    _, sqlserver_credit = get_credit_info(um.content)

    #############################################
    # clientid, clientname, agent, instance, os #
    #############################################
    dm = SQLApi.CVApi(sqlserver_credit)

    oracle_data = dm.get_instance_from_oracle()

    # 获取包含oracle模块所有客户端
    installed_client = dm.get_all_install_clients()
    dm.close()
    oracle_client_list = []
    pre_od_name = ""
    for od in oracle_data:
        if "Oracle" in od["agent"]:
            if od["clientname"] == pre_od_name:
                continue
            client_id = od["clientid"]
            client_os = ""
            for ic in installed_client:
                if client_id == ic["client_id"]:
                    client_os = ic["os"]

            oracle_client_list.append({
                "clientid": od["clientid"],
                "clientname": od["clientname"],
                "agent": od["agent"],
                "instance": od["instance"],
                "os": client_os
            })
            # 去重
            pre_od_name = od["clientname"]
    return {
        'utils_manage': um.id,
        'oracle_client': oracle_client_list
    }


# 恢复资源
@login_required
def target(request, funid):
    # 工具
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    data = []

    try:
        pool = ThreadPoolExecutor(max_workers=10)

        all_tasks = [pool.submit(get_oracle_client, (um)) for um in utils_manage]
        for future in as_completed(all_tasks):
            if future.result():
                data.append(future.result())
    except:
        pass

    return render(request, 'target.html',
                  {'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
                   "data": json.dumps(data),
                   "pagefuns": getpagefuns(funid, request=request)})


# @login_required
# def get_orcl_client_from_utils(request):
#     status = 1
#     info = '获取成功。'
#     data = []
#
#     utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
#
#     def get_oracle_client(um):
#         # 解析出账户信息
#         _, sqlserver_credit = get_credit_info(um.content)
#
#         #############################################
#         # clientid, clientname, agent, instance, os #
#         #############################################
#         dm = SQLApi.CVApi(sqlserver_credit)
#
#         oracle_data = dm.get_instance_from_oracle()
#
#         # 获取包含oracle模块所有客户端
#         installed_client = dm.get_all_install_clients()
#         dm.close()
#         oracle_client_list = []
#         pre_od_name = ""
#         for od in oracle_data:
#             if "Oracle" in od["agent"]:
#                 if od["clientname"] == pre_od_name:
#                     continue
#                 client_id = od["clientid"]
#                 client_os = ""
#                 for ic in installed_client:
#                     if client_id == ic["client_id"]:
#                         client_os = ic["os"]
#
#                 oracle_client_list.append({
#                     "clientid": od["clientid"],
#                     "clientname": od["clientname"],
#                     "agent": od["agent"],
#                     "instance": od["instance"],
#                     "os": client_os
#                 })
#                 # 去重
#                 pre_od_name = od["clientname"]
#         return {
#             'utils_manage': um.id,
#             'oracle_client': oracle_client_list
#         }
#
#     try:
#         pool = ThreadPoolExecutor(max_workers=10)
#
#         all_tasks = [pool.submit(get_oracle_client, (um)) for um in utils_manage]
#         for future in as_completed(all_tasks):
#             if future.result():
#                 data.append(future.result())
#     except Exception as e:
#         print(e)
#         status = 0
#         info = '获取客户端信息失败: {e}。'.format(**{'e': e})
#
#     return JsonResponse({
#         'status': status,
#         'info': info,
#         'data': data,
#     })


@login_required
def target_data(request):
    all_target = Target.objects.exclude(state="9").select_related('utils')
    all_target_list = []
    for target in all_target:
        target_info = json.loads(target.info)
        all_target_list.append({
            "id": target.id,
            "client_id": target.client_id,
            "client_name": target.client_name,
            "os": target.os,
            "agent": target_info["agent"],
            "instance": target_info["instance"],
            "utils_id": target.utils_id,
            "utils_name": target.utils.name if target.utils else ''
        })
    return JsonResponse({"data": all_target_list})


@login_required
def target_save(request):
    target_id = request.POST.get("target_id", "")
    client_id = request.POST.get("client_id", "")
    client_name = request.POST.get("client_name", "").strip()
    agent = request.POST.get("agent", "").strip()
    instance = request.POST.get("instance", "").strip()
    os = request.POST.get("os", "").strip()
    utils_manage = request.POST.get("utils_manage", "").strip()
    ret = 0
    info = ""
    try:
        target_id = int(target_id)
    except:
        ret = 0
        info = "网络异常。"
    else:
        try:
            utils_manage = int(utils_manage)
        except:
            ret = 0
            info = "工具未选择。"
        else:
            try:
                client_id = int(client_id)
            except:
                ret = 0
                info = "目标客户端未选择。"
            else:
                if target_id == 0:
                    # 判断是否存在
                    check_target = Target.objects.exclude(state="9").filter(client_id=client_id)
                    if check_target.exists():
                        ret = 0
                        info = "该客户端已选为目标客户端，请勿重复添加。"
                    else:
                        try:
                            cur_target = Target()
                            cur_target.client_id = client_id
                            cur_target.client_name = client_name
                            cur_target.os = os
                            cur_target.utils_id = utils_manage
                            cur_target.info = json.dumps({
                                "agent": agent,
                                "instance": instance
                            })
                            cur_target.save()
                        except:
                            ret = 0
                            info = "数据保存失败。"
                        else:
                            ret = 1
                            info = "新增成功。"
                else:
                    check_target = Target.objects.exclude(state="9").exclude(id=target_id).filter(
                        client_id=client_id)
                    if check_target.exists():
                        ret = 0
                        info = "该客户端已选为终端，请勿重复添加。"
                    else:
                        try:
                            cur_target = Target.objects.get(id=target_id)
                        except Target.DoesNotExist as e:
                            ret = 0
                            info = "终端不存在，请联系管理员。"
                        else:
                            try:
                                cur_target.client_id = client_id
                                cur_target.client_name = client_name
                                cur_target.os = os
                                cur_target.utils_id = utils_manage
                                cur_target.info = json.dumps({
                                    "agent": agent,
                                    "instance": instance
                                })
                                cur_target.save()
                            except:
                                ret = 0
                                info = "数据修改失败。"
                            else:
                                ret = 1
                                info = "修改成功"

    return JsonResponse({
        "ret": ret,
        "info": info
    })


@login_required
def target_del(request):
    target_id = request.POST.get("target_id", "")

    try:
        cur_target = Target.objects.get(id=int(target_id))
    except:
        return JsonResponse({
            "ret": 0,
            "info": "当前网络异常"
        })
    else:
        try:
            cur_target.state = "9"
            cur_target.save()
        except:
            return JsonResponse({
                "ret": 0,
                "info": "服务器网络异常。"
            })
        else:
            return JsonResponse({
                "ret": 1,
                "info": "删除成功。"
            })


@login_required
def origin(request, funid):
    # 工具
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    data = []

    try:
        pool = ThreadPoolExecutor(max_workers=10)

        all_tasks = [pool.submit(get_oracle_client, (um)) for um in utils_manage]
        for future in as_completed(all_tasks):
            if future.result():
                data.append(future.result())
    except:
        pass

    # 所有关联终端
    all_target = Target.objects.exclude(state="9").values()

    u_targets = []

    for um in utils_manage:
        target_list = []
        for target in all_target:
            if target['utils_id'] == um.id:
                target_list.append({
                    'target_id': target['id'],
                    'target_name': target['client_name']
                })
        u_targets.append({
            'utils_manage': um.id,
            'target_list': target_list
        })

    # 恢复资源
    # [{
    #     'utils_manage': '',
    #     'target_list': [{
    #         'target_id': '',
    #         'target_name': ''
    #     }]
    # }]

    return render(request, 'origin.html',
                  {'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
                   "data": json.dumps(data), "all_target": all_target, 'u_targets': u_targets,
                   "pagefuns": getpagefuns(funid, request=request)})


@login_required
def origin_data(request):
    all_origin = Origin.objects.exclude(state="9").select_related("target")
    all_origin_list = []
    for origin in all_origin:
        origin_info = json.loads(origin.info)
        all_origin_list.append({
            "id": origin.id,
            "client_id": origin.client_id,
            "client_name": origin.client_name,
            "os": origin.os,
            "agent": origin_info["agent"],
            "instance": origin_info["instance"],
            "target_client": origin.target.id,
            "target_client_name": origin.target.client_name,
            "copy_priority": origin.copy_priority,
            "db_open": origin.db_open,
            "data_path": origin.data_path,
            "log_restore": origin.log_restore,

            "utils_id": origin.utils_id,
            "utils_name": origin.utils.name if origin.utils else ''
        })

    return JsonResponse({"data": all_origin_list})


@login_required
def origin_save(request):
    origin_id = request.POST.get("origin_id", "")
    client_id = request.POST.get("client_id", "")
    client_name = request.POST.get("client_name", "").strip()
    agent = request.POST.get("agent", "").strip()
    instance = request.POST.get("instance", "").strip()
    client_os = request.POST.get("os", "")
    target_client = request.POST.get("target_client", "")

    copy_priority = request.POST.get("copy_priority", "")
    db_open = request.POST.get("db_open", "")
    data_path = request.POST.get("data_path", "")
    log_restore = request.POST.get("log_restore", "")

    utils_manage = request.POST.get("utils_manage", "").strip()
    ret = 0
    info = ""
    try:
        copy_priority = int(copy_priority)
        db_open = int(db_open)
        origin_id = int(origin_id)
    except:
        ret = 0
        info = "网络异常"
    else:
        try:
            utils_manage = int(utils_manage)
        except:
            ret = 0
            info = "工具未选择。"
        else:
            try:
                client_id = int(client_id)
            except:
                ret = 0
                info = "源端未选择。"
            else:
                try:
                    target_client = int(target_client)
                except:
                    ret = 0
                    info = "未关联终端"
                else:
                    try:
                        to_target = Target.objects.get(id=target_client)
                    except Target.DoesNotExist as e:
                        ret = 0
                        info = "该终端不存在。"
                    else:
                        target_id = to_target.id
                        if origin_id == 0:
                            try:
                                cur_origin = Origin()
                                cur_origin.client_id = client_id
                                cur_origin.client_name = client_name
                                cur_origin.os = client_os
                                cur_origin.info = json.dumps({
                                    "agent": agent,
                                    "instance": instance
                                })
                                cur_origin.target_id = target_id
                                cur_origin.copy_priority = copy_priority
                                cur_origin.db_open = db_open
                                cur_origin.data_path = data_path

                                cur_origin.utils_id = utils_manage

                                try:
                                    log_restore = int(log_restore)
                                except:
                                    pass
                                else:
                                    cur_origin.log_restore = log_restore
                                cur_origin.save()
                            except Exception as e:
                                print(e)
                                ret = 0
                                info = "数据保存失败。"
                            else:
                                ret = 1
                                info = "新增成功。"
                        else:
                            try:
                                cur_origin = Origin.objects.get(id=origin_id)
                            except Origin.DoesNotExist as e:
                                ret = 0
                                info = "源端不存在，请联系管理员。"
                            else:
                                try:
                                    cur_origin.client_id = client_id
                                    cur_origin.client_name = client_name
                                    cur_origin.os = client_os
                                    cur_origin.info = json.dumps({
                                        "agent": agent,
                                        "instance": instance
                                    })
                                    cur_origin.copy_priority = copy_priority
                                    cur_origin.db_open = db_open
                                    cur_origin.data_path = data_path
                                    cur_origin.target_id = target_id

                                    cur_origin.utils_id = utils_manage

                                    try:
                                        log_restore = int(log_restore)
                                    except:
                                        pass
                                    else:
                                        cur_origin.log_restore = log_restore
                                    cur_origin.save()
                                except:
                                    ret = 0
                                    info = "数据修改失败。"
                                else:
                                    ret = 1
                                    info = "修改成功"

    return JsonResponse({
        "ret": ret,
        "info": info
    })


@login_required
def origin_del(request):
    origin_id = request.POST.get("origin_id", "")
    try:
        cur_origin = Origin.objects.get(id=int(origin_id))
    except:
        return JsonResponse({
            "ret": 0,
            "info": "当前网络异常"
        })
    else:
        try:
            cur_origin.state = "9"
            cur_origin.save()
        except:
            return JsonResponse({
                "ret": 0,
                "info": "服务器网络异常。"
            })
        else:
            return JsonResponse({
                "ret": 1,
                "info": "删除成功。"
            })


def get_rowspan(whole_list, **kwargs):
    clientname = kwargs.get('clientname', '')
    idataagent = kwargs.get('idataagent', '')
    type = kwargs.get('type', '')
    subclient = kwargs.get('subclient', '')

    scheduePolicy = kwargs.get('scheduePolicy', '')
    schedbackuptype = kwargs.get('schedbackuptype', '')

    row_span = 0

    if clientname and not any([idataagent, type, subclient, scheduePolicy, schedbackuptype]):
        for tl in whole_list:
            if tl['clientname'] == clientname:
                row_span += 1
    if all([clientname, idataagent]) and not any([type, subclient, scheduePolicy, schedbackuptype]):
        for tl in whole_list:
            if tl['clientname'] == clientname and tl['idataagent'] == idataagent:
                row_span += 1
    if all([clientname, idataagent, type]) and not any([subclient, scheduePolicy, schedbackuptype]):
        for tl in whole_list:
            if tl['clientname'] == clientname and tl['idataagent'] == idataagent and tl['type'] == type:
                row_span += 1
    if all([clientname, idataagent, type, subclient]) and not any([scheduePolicy, schedbackuptype]):
        for tl in whole_list:
            if tl['clientname'] == clientname and tl['idataagent'] == idataagent and tl['type'] == type and tl[
                'subclient'] == subclient:
                row_span += 1
    if all([clientname, idataagent, type, subclient, scheduePolicy]) and not schedbackuptype:
        for tl in whole_list:
            if tl['clientname'] == clientname and tl['idataagent'] == idataagent and tl['type'] == type and tl[
                'subclient'] == subclient and tl['scheduePolicy'] == scheduePolicy:
                row_span += 1
    if all([clientname, idataagent, type, subclient, scheduePolicy, schedbackuptype]):
        for tl in whole_list:
            if tl['clientname'] == clientname and tl['idataagent'] == idataagent and tl['type'] == type and tl[
                'subclient'] == subclient and tl['scheduePolicy'] == scheduePolicy and tl[
                'schedbackuptype'] == schedbackuptype:
                row_span += 1
    return row_span


@login_required
def get_backup_status(request):
    whole_list = []
    utils_manage_id = request.POST.get('utils_manage_id', '')

    try:
        utils_manage_id = int(utils_manage_id)
        utils_manage = UtilsManage.objects.get(id=utils_manage_id)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            # 仅统计源客户端(客户端管理)
            all_client_manage = Origin.objects.exclude(state="9").values("client_name")
            tmp_client_manage = [tmp_client["client_name"] for tmp_client in all_client_manage]

            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_backup_status(tmp_client_manage)

            for num, wl in enumerate(whole_list):
                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])
                # 时间
                try:
                    whole_list[num]["startdate"] = "{:%Y-%m-%d %H:%M:%S}".format(whole_list[num]["startdate"])
                except Exception as e:
                    whole_list[num]["startdate"] = ""

                whole_list[num]['clientname_rowspan'] = clientname_rowspan
                whole_list[num]['idataagent_rowspan'] = idataagent_rowspan
                whole_list[num]['type_rowspan'] = type_rowspan

            dm.close()
        except Exception as e:
            return JsonResponse({
                "ret": 0,
                "data": "获取备份状态信息失败。",
            })
        return JsonResponse({
            "ret": 1,
            "data": whole_list,
        })


@login_required
def backup_status(request, funid):
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    return render(request, "backup_status.html", {
        'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
        "pagefuns": getpagefuns(funid, request),
    })


@login_required
def get_backup_content(request):
    utils_manage_id = request.POST.get('utils_manage_id', '')

    try:
        utils_manage_id = int(utils_manage_id)
        utils_manage = UtilsManage.objects.get(id=utils_manage_id)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)

        whole_list = []
        try:
            all_client_manage = Origin.objects.exclude(state="9").values("client_name")
            tmp_client_manage = [tmp_client["client_name"] for tmp_client in all_client_manage]

            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_backup_content(tmp_client_manage)

            for num, wl in enumerate(whole_list):
                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])

                whole_list[num]['clientname_rowspan'] = clientname_rowspan
                whole_list[num]['idataagent_rowspan'] = idataagent_rowspan
                whole_list[num]['type_rowspan'] = type_rowspan

        except Exception as e:
            print(e)
            return JsonResponse({
                "ret": 0,
                "data": "获取存储策略信息失败。",
            })
        else:
            return JsonResponse({
                "ret": 1,
                "data": whole_list,
            })


@login_required
def backup_content(request, funid):
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')

    return render(request, "backup_content.html", {
        'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
        "pagefuns": getpagefuns(funid, request),
    })


@login_required
def get_storage_policy(request):
    whole_list = []
    utils_manage_id = request.POST.get('utils_manage_id', '')

    try:
        utils_manage_id = int(utils_manage_id)
        utils_manage = UtilsManage.objects.get(id=utils_manage_id)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            all_client_manage = Origin.objects.exclude(state="9").values("client_name")
            tmp_client_manage = [tmp_client["client_name"] for tmp_client in all_client_manage]

            dm = SQLApi.CVApi(sqlserver_credit)

            whole_list = dm.get_storage_policy(tmp_client_manage)

            for num, wl in enumerate(whole_list):
                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])

                whole_list[num]['clientname_rowspan'] = clientname_rowspan
                whole_list[num]['idataagent_rowspan'] = idataagent_rowspan
                whole_list[num]['type_rowspan'] = type_rowspan

        except Exception as e:
            print(e)
            return JsonResponse({
                "ret": 0,
                "data": "获取存储策略信息失败。",
            })
        else:
            return JsonResponse({
                "ret": 1,
                "data": whole_list
            })


@login_required
def storage_policy(request, funid):
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    return render(request, "storage_policy.html", {
        'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
        "pagefuns": getpagefuns(funid, request),
    })


@login_required
def schedule_policy(request, funid):
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    return render(request, "schedule_policy.html", {
        'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
        "pagefuns": getpagefuns(funid, request),
    })


@login_required
def get_schedule_policy(request):
    whole_list = []
    utils_manage_id = request.POST.get('utils_manage_id', '')

    try:
        utils_manage_id = int(utils_manage_id)
        utils_manage = UtilsManage.objects.get(id=utils_manage_id)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            all_client_manage = Origin.objects.exclude(state="9").values("client_name")
            tmp_client_manage = [tmp_client["client_name"] for tmp_client in all_client_manage]

            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_schedule_policy(tmp_client_manage)
            ordered_whole_list = []
            dm.close()
            for num, wl in enumerate(whole_list):

                schedule_dict = OrderedDict()

                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])
                # 子客户端，计划策略，备份类型
                subclient_rowspan = get_rowspan(whole_list, clientname=wl['clientname'],
                                                idataagent=wl['idataagent'],
                                                type=wl['type'], subclient=wl['subclient'])
                if wl['scheduePolicy']:
                    scheduePolicy_rowspan = get_rowspan(whole_list, clientname=wl['clientname'],
                                                        idataagent=wl['idataagent'],
                                                        type=wl['type'], subclient=wl['subclient'],
                                                        scheduePolicy=wl['scheduePolicy'])
                else:
                    scheduePolicy_rowspan = 1
                if wl['schedbackuptype'] and wl['scheduePolicy']:
                    schedbackuptype_rowspan = get_rowspan(whole_list, clientname=wl['clientname'],
                                                          idataagent=wl['idataagent'],
                                                          type=wl['type'], subclient=wl['subclient'],
                                                          scheduePolicy=wl['scheduePolicy'],
                                                          schedbackuptype=wl['schedbackuptype'])
                else:
                    schedbackuptype_rowspan = 1
                schedule_dict['clientname_rowspan'] = clientname_rowspan
                schedule_dict['idataagent_rowspan'] = idataagent_rowspan
                schedule_dict['type_rowspan'] = type_rowspan
                schedule_dict['subclient_rowspan'] = subclient_rowspan
                schedule_dict['scheduePolicy_rowspan'] = scheduePolicy_rowspan
                schedule_dict['schedbackuptype_rowspan'] = schedbackuptype_rowspan

                schedule_dict["clientname"] = wl["clientname"]
                schedule_dict["idataagent"] = wl["idataagent"]
                schedule_dict["type"] = wl["type"]
                schedule_dict["subclient"] = wl["subclient"]
                schedule_dict["scheduePolicy"] = wl["scheduePolicy"] if wl["scheduePolicy"] else "无"
                schedule_dict["schedbackuptype"] = wl["schedbackuptype"] if wl["schedbackuptype"] else "无"
                schedule_dict["schedpattern"] = wl["schedpattern"] if wl["schedpattern"] else "无"

                schedule_dict["option"] = {
                    "schedpattern": wl["schedpattern"],
                    "schednextbackuptime": wl["schednextbackuptime"],
                    "scheduleName": wl["scheduleName"],
                    "schedinterval": wl["schedinterval"],
                    "schedbackupday": wl["schedbackupday"],
                    "schedbackuptype": wl["schedbackuptype"],
                }

                ordered_whole_list.append(schedule_dict)

        except Exception as e:
            print(e)
            return JsonResponse({
                "ret": 0,
                "data": "获取计划策略信息失败。",
            })
        else:
            return JsonResponse({
                "ret": 1,
                "data": ordered_whole_list,
            })


@login_required
def disk_space(request, funid):
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    return render(request, 'disk_space.html', {
        'username': request.user.userinfo.fullname, 'utils_manage': utils_manage,
        "pagefuns": getpagefuns(funid, request=request)
    })


@login_required
def get_disk_space(request):
    # MA rowspan 总记录数
    # 库 rowspan 相同库记录数
    status = 1
    data = []
    info = ''
    utils_manage_id = request.POST.get('utils_manage_id', '')

    try:
        utils_manage_id = int(utils_manage_id)
        utils_manage = UtilsManage.objects.get(id=utils_manage_id)
    except:
        status = 0
        info = 'Commvault工具未配置。'
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            dm = SQLApi.CVApi(sqlserver_credit)
            data = dm.get_library_space_info()
            dm.close()

            # 遍历所有记录 总记录数
            def get_rowspan(total_list, **kwargs):
                row_span = 0
                display_name = kwargs.get('DisplayName', '')
                library_name = kwargs.get('LibraryName', '')
                if all([display_name, library_name]):
                    for tl in total_list:
                        if tl['DisplayName'] == display_name and tl['LibraryName'] == library_name:
                            row_span += 1
                if display_name and not library_name:
                    for tl in total_list:
                        if tl['DisplayName'] == display_name:
                            row_span += 1
                return row_span

            for num, lsi in enumerate(data):
                display_name_rowspan = get_rowspan(data, DisplayName=lsi['DisplayName'])
                library_name_rowspan = get_rowspan(data, DisplayName=lsi['DisplayName'], LibraryName=lsi['LibraryName'])

                # 时间
                try:
                    data[num]["LastBackupTime"] = "{:%Y-%m-%d %H:%M:%S}".format(data[num]["LastBackupTime"])
                except Exception as e:
                    data[num]["LastBackupTime"] = ""
                # 是否可用
                if data[num]["Offline"] == 0:
                    data[num]["Offline"] = '<i class="fa fa-plug" style="color:green; height:20px;width:14px;"></i>'
                else:
                    data[num]["Offline"] = '<i class="fa fa-plug" style="color:red; height:20px;width:14px;"></i>'

                data[num]['display_name_rowspan'] = display_name_rowspan
                data[num]['library_name_rowspan'] = library_name_rowspan

        except Exception as e:
            print(e)
            status = 0
            info = '获取磁盘容量信息失败: {e}。'.format(e=e)
    return JsonResponse({
        "status": status,
        "info": info,
        "data": data
    })


@login_required
def get_disk_space_daily(request):
    disk_list = []

    media_id = request.POST.get("media_id", "")
    utils_id = request.POST.get("utils_id", "")

    try:
        media_id = int(media_id)
    except:
        pass
    try:
        utils_id = int(utils_id)
    except:
        pass
    if media_id:
        disk_space_weekly_data = DiskSpaceWeeklyData.objects.filter(utils_id=utils_id, media_id=media_id).values()
        capacity_available_list = []
        space_reserved_list = []
        total_space_list = []

        if disk_space_weekly_data:
            for num, dswd in enumerate(disk_space_weekly_data):
                if num > 20:
                    break

                capacity_available_list.append(round(dswd["capacity_avaible"] / 1024, 2))
                space_reserved_list.append(round(dswd["space_reserved"] / 1024, 2))
                total_space_list.append(round(dswd["total_space"] / 1024, 2))

            disk_list.append({
                "name": "可用容量",
                "color": "#3598dc",
                "capacity_list": capacity_available_list
            })
            disk_list.append({
                "name": "保留空间容量",
                "color": "#e7505a",
                "capacity_list": space_reserved_list
            })
            disk_list.append({
                "name": "总容量",
                "color": "#32c5d2",
                "capacity_list": total_space_list
            })
    else:
        # 总
        disk_space_weekly_data = DiskSpaceWeeklyData.objects.filter(utils_id=utils_id).values(
            "utils_id", "capacity_avaible", "space_reserved", "total_space", "point_tag"
        )
        capacity_available_list = []
        space_reserved_list = []
        total_space_list = []
        if disk_space_weekly_data:
            pre_point_tag = ""
            num = 0
            for dswd in disk_space_weekly_data:
                if num > 20:
                    break
                # util_id 与 相同记录的 数据相加
                if dswd["point_tag"] == pre_point_tag:
                    continue
                num += 1

                cur_disk_space_weekly_data = [i for i in disk_space_weekly_data if
                                              i["utils_id"] == utils_id and i["point_tag"] == dswd["point_tag"]]

                sum_capacity_avaible = 0
                sum_space_reserved = 0
                sum_total_space = 0
                for cdswd in cur_disk_space_weekly_data:
                    sum_capacity_avaible += cdswd["capacity_avaible"]
                    sum_space_reserved += cdswd["space_reserved"]
                    sum_total_space += cdswd["total_space"]

                capacity_available_list.append(round(sum_capacity_avaible / 1024, 2))
                space_reserved_list.append(round(sum_space_reserved / 1024, 2))
                total_space_list.append(round(sum_total_space / 1024, 2))

                pre_point_tag = dswd["point_tag"]
            disk_list.append({
                "name": "可用容量",
                "color": "#3598dc",
                "capacity_list": capacity_available_list
            })
            disk_list.append({
                "name": "保留空间容量",
                "color": "#e7505a",
                "capacity_list": space_reserved_list
            })
            disk_list.append({
                "name": "总容量",
                "color": "#32c5d2",
                "capacity_list": total_space_list
            })

    return JsonResponse({
        "data": disk_list,
    })


@login_required
def get_ma_disk_space(request):
    """
    获取总容量
    :param request:
    :return:
    """
    status = 1
    data = []
    info = ''
    utils_id = request.POST.get('utils_id', '')

    try:
        utils_id = int(utils_id)
        utils_manage = UtilsManage.objects.get(id=utils_id)
    except:
        status = 0
        info = 'Commvault工具未配置。'
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            dm = SQLApi.CVApi(sqlserver_credit)
            ret = dm.get_library_space_info()
            dm.close()
            capacity_available = 0
            space_reserved = 0
            total_space = 0

            for r in ret:
                if type(r["CapacityAvailable"]) == int:
                    capacity_available += r["CapacityAvailable"]
                if type(r["SpaceReserved"]) == int:
                    space_reserved += r["SpaceReserved"]
                if type(r["TotalSpaceMB"]) == int:
                    total_space += r["TotalSpaceMB"]

            capacity_available_percent = round((capacity_available / total_space) * 100, 0)
            space_reserved_percent = round((space_reserved / total_space) * 100, 0)
            used_space_percent = 100 - capacity_available_percent - space_reserved_percent
            data.append({
                "name": "可用容量",
                "y": capacity_available_percent
            })
            data.append({
                "name": "保留空间",
                "y": space_reserved_percent
            })
            data.append({
                "name": "已用空间",
                "y": used_space_percent
            })
        except:
            pass
    return JsonResponse({
        "status": status,
        "info": info,
        "data": data
    })


@login_required
def oraclerecoverydata(request):
    origin_id = request.GET.get('origin_id', '')
    result = []
    try:
        origin_id = int(origin_id)
        origin = Origin.objects.get(id=origin_id)
        utils_manage = origin.utils
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        dm = SQLApi.CVApi(sqlserver_credit)
        result = dm.get_oracle_backup_job_list(origin.client_name)
        dm.close()
    except Exception as e:
        print(e)

    return JsonResponse({"data": result})


@login_required
def process_schedule(request, funid):
    all_process = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")).order_by("sort").only("id",
                                                                                                              "name")

    return render(request, 'process_schedule.html', {'username': request.user.userinfo.fullname,
                                                     "pagefuns": getpagefuns(funid, request=request),
                                                     "all_process": all_process})


@login_required
def process_schedule_save(request):
    process_schedule_id = request.POST.get('process_schedule_id', '')
    process_schedule_name = request.POST.get('process_schedule_name', '')
    process = request.POST.get('process', '')
    process_schedule_remark = request.POST.get('process_schedule_remark', '')

    schedule_type = request.POST.get('schedule_type', '')

    per_time = request.POST.get('per_time', '')
    per_month = request.POST.get('per_month', '')
    per_week = request.POST.get('per_week', '')
    ret = 1
    info = ""

    if not process_schedule_name:
        return JsonResponse({
            "ret": 0,
            "info": "计划名称不能为空。"
        })

    try:
        process = int(process)
    except ValueError as e:
        return JsonResponse({
            "ret": 0,
            "info": "流程未选择。"
        })

    try:
        process_schedule_id = int(process_schedule_id)
    except ValueError as e:
        return JsonResponse({
            "ret": 0,
            "info": "网络异常。"
        })

    # 周期类型
    try:
        schedule_type = int(schedule_type)
    except ValueError as e:
        return JsonResponse({
            "ret": 0,
            "info": "周期类型未选择。"
        })
    else:
        if schedule_type == 2:
            per_month = "*"
            if not per_week:
                return JsonResponse({
                    "ret": 0,
                    "info": "周几未选择。"
                })

        if schedule_type == 3:
            per_week = "*"
            if not per_month:
                return JsonResponse({
                    "ret": 0,
                    "info": "每月第几天未选择。"
                })

    try:
        cur_process = Process.objects.get(id=process)
    except Process.DoesNotExist as e:
        ret = 0
        info = "流程不存在。"
    else:
        if not per_time:
            ret = 0
            info = "时间未填写。"
        else:
            # 保存定时任务
            hour, minute = per_time.split(':')
            # 新增
            if process_schedule_id == 0:
                cur_crontab_schedule = CrontabSchedule()
                cur_crontab_schedule.hour = hour
                cur_crontab_schedule.minute = minute
                cur_crontab_schedule.day_of_week = per_week if per_week else "*"
                cur_crontab_schedule.day_of_month = per_month if per_month else "*"

                cur_crontab_schedule.save()
                cur_crontab_schedule_id = cur_crontab_schedule.id

                # 启动定时任务
                cur_periodictask = PeriodicTask()
                cur_periodictask.crontab_id = cur_crontab_schedule_id
                cur_periodictask.name = uuid.uuid1()
                # 默认关闭
                cur_periodictask.enabled = 0
                # 任务名称
                cur_periodictask.task = "faconstor.tasks.create_process_run"
                # cur_periodictask.args = [cur_process.id, request]
                cur_periodictask.kwargs = json.dumps({
                    'cur_process': cur_process.id,
                    'creatuser': request.user.username
                })
                cur_periodictask.save()
                cur_periodictask_id = cur_periodictask.id

                ps = ProcessSchedule()
                ps.dj_periodictask_id = cur_periodictask_id
                ps.process = cur_process
                ps.name = process_schedule_name
                ps.remark = process_schedule_remark
                ps.schedule_type = schedule_type
                ps.save()
                ret = 1
                info = "保存成功。"
            else:
                # 修改
                try:
                    ps = ProcessSchedule.objects.get(id=process_schedule_id)
                except ProcessSchedule.DoesNotExist as e:
                    ret = 0
                    info = "计划流程不存在。"
                else:

                    cur_periodictask_id = ps.dj_periodictask_id
                    # 启动定时任务
                    try:
                        cur_periodictask = PeriodicTask.objects.get(id=cur_periodictask_id)
                    except PeriodicTask.DoesNotExist as e:
                        ret = 0
                        info = "定时任务不存在。"
                    else:
                        cur_crontab_schedule = cur_periodictask.crontab
                        cur_crontab_schedule.hour = hour
                        cur_crontab_schedule.minute = minute
                        cur_crontab_schedule.day_of_week = per_week if per_week else "*"
                        cur_crontab_schedule.day_of_month = per_month if per_month else "*"
                        cur_crontab_schedule.save()
                        # 刷新定时器状态
                        cur_periodictask.task = "faconstor.tasks.create_process_run"
                        cur_periodictask.kwargs = json.dumps({
                            'cur_process': cur_process.id,
                            'creatuser': request.user.username
                        })
                        cur_periodictask_status = cur_periodictask.enabled
                        cur_periodictask.enabled = cur_periodictask_status
                        cur_periodictask.save()

                        ps.process = cur_process
                        ps.name = process_schedule_name
                        ps.remark = process_schedule_remark
                        ps.schedule_type = schedule_type

                        ps.save()
                        ret = 1
                        info = "保存成功。"
    return JsonResponse({
        "ret": ret,
        "info": info
    })


@login_required
def process_schedule_data(request):
    result = []

    all_process_schedules = ProcessSchedule.objects.exclude(state="9").select_related("process", "dj_periodictask",
                                                                                      "dj_periodictask__crontab")

    for process_schedule in all_process_schedules:
        process_id = process_schedule.process.id
        process_name = process_schedule.process.name
        remark = process_schedule.remark
        schedule_type = process_schedule.schedule_type
        schedule_type_display = process_schedule.get_schedule_type_display()
        # 定时任务
        status, minutes, hours, per_week, per_month = "", "", "", "", ""
        periodictask = process_schedule.dj_periodictask
        if periodictask:
            status = periodictask.enabled
            cur_crontab_schedule = periodictask.crontab
            if cur_crontab_schedule:
                minutes = cur_crontab_schedule.minute
                hours = cur_crontab_schedule.hour
                per_week = cur_crontab_schedule.day_of_week
                per_month = cur_crontab_schedule.day_of_month

        result.append({
            "process_schedule_id": process_schedule.id,
            "process_schedule_name": process_schedule.name,
            "process_id": process_id,
            "process_name": process_name,
            "remark": remark,
            "schedule_type": schedule_type,
            "schedule_type_display": schedule_type_display,
            "minutes": minutes,
            "hours": hours,
            "per_week": per_week,
            "per_month": per_month,
            "status": status,
        })
    return JsonResponse({"data": result})


@login_required
def change_periodictask(request):
    process_schedule_id = request.POST.get("process_schedule_id", "")
    process_periodictask_status = request.POST.get("process_periodictask_status", "")
    try:
        process_schedule_id = int(process_schedule_id)
        process_periodictask_status = int(process_periodictask_status)
    except ValueError as e:
        return JsonResponse({
            "ret": 0,
            "info": "网络异常。"
        })

    try:
        cur_process_schedule = ProcessSchedule.objects.get(id=process_schedule_id)
    except ProcessSchedule.DoesNotExist as e:
        return JsonResponse({
            "ret": 0,
            "info": "该计划流程不存在。"
        })
    else:
        cur_periodictask = cur_process_schedule.dj_periodictask
        if cur_periodictask:
            cur_periodictask.enabled = process_periodictask_status
            cur_periodictask.save()
            return JsonResponse({
                "ret": 1,
                "info": "定时任务状态修改成功。"
            })
        else:
            return JsonResponse({
                "ret": 0,
                "info": "该计划流程对应的定时任务不存在。"
            })


@login_required
def process_schedule_del(request):
    process_schedule_id = request.POST.get("process_schedule_id", "")

    try:
        process_schedule_id = int(process_schedule_id)
    except ValueError as e:
        return JsonResponse({
            "ret": 0,
            "info": "网络异常。"
        })

    ret = 1
    info = "流程计划删除成功。"
    # 删除process_schedule/crontab/periodictask
    try:
        cur_process_schedule = ProcessSchedule.objects.get(id=process_schedule_id)
    except ProcessSchedule.DoesNotExist as e:
        ret = 0
        info = "该流程计划不存在。"
    else:
        cur_process_schedule.state = "9"
        cur_process_schedule.save()

        try:
            cur_process_schedule.dj_periodictask.crontab.delete()
            cur_process_schedule.dj_periodictask.delete()
        except:
            ret = 0
            info = "定时任务删除失败。"
    return JsonResponse({
        "ret": ret,
        "info": info
    })


@login_required
def manualrecovery(request, funid):
    result = []
    all_targets = Target.objects.exclude(state="9")
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    return render(request, 'manualrecovery.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                   "all_targets": all_targets, "utils_manage": utils_manage})


@login_required
def manualrecoverydata(request):
    utils_manage_id = request.GET.get("utils_manage_id", "")
    result = []

    try:
        utils_manage_id = int(utils_manage_id)
    except Exception as e:
        print(e)
    else:
        all_origins = Origin.objects.exclude(state="9").filter(utils_id=utils_manage_id).select_related("target")
        for origin in all_origins:
            result.append({
                "client_manage_id": origin.id,
                "client_name": origin.client_name,
                "client_id": origin.client_id,
                "client_os": origin.os,
                "model": json.loads(origin.info)["agent"],
                "data_path": origin.data_path if origin.data_path else "",
                "copy_priority": origin.copy_priority,
                "target_client": origin.target.client_name
            })
    return JsonResponse({"data": result})


@login_required
def dooraclerecovery(request):
    if request.method == 'POST':
        sourceClient = request.POST.get('sourceClient', '')
        destClient = request.POST.get('destClient', '')
        restoreTime = request.POST.get('restoreTime', '')
        browseJobId = request.POST.get('browseJobId', '')
        agent = request.POST.get('agent', '')
        data_path = request.POST.get('data_path', '')
        copy_priority = request.POST.get('copy_priority', '')

        try:
            copy_priority = int(copy_priority)
        except:
            pass

        data_sp = request.POST.get('data_sp', '')

        #################################
        # sourceClient>> instance_name  #
        #################################
        instance = ""
        try:
            cur_origin = Origin.objects.exclude(state="9").get(client_name=sourceClient)
        except Origin.DoesNotExist as e:
            return HttpResponse("恢复任务启动失败, 源客户端不存在。")
        else:
            oracle_info = json.loads(cur_origin.info)

            if oracle_info:
                try:
                    instance = oracle_info["instance"]
                except:
                    pass
            if not instance:
                return HttpResponse("恢复任务启动失败, 数据库实例不存在。")

            utils_content = cur_origin.utils.content if cur_origin.utils else ""
            commvault_credit, sqlserver_credit = get_credit_info(utils_content)

            # restoreTime对应curSCN号
            dm = SQLApi.CVApi(sqlserver_credit)
            oraclecopys = dm.get_oracle_backup_job_list(sourceClient)
            # print("> %s" % restoreTime)
            curSCN = ""
            if restoreTime:
                for i in oraclecopys:
                    if i["subclient"] == "default" and i['LastTime'] == restoreTime:
                        # print('>>>>>1')
                        print(i['LastTime'])
                        curSCN = i["cur_SCN"]
                        break
            else:
                for i in oraclecopys:
                    if i["subclient"] == "default":
                        # print('>>>>>2')
                        curSCN = i["cur_SCN"]
                        break

            if copy_priority == 2:
                # 辅助拷贝状态
                auxcopys = dm.get_all_auxcopys()
                jobs_controller = dm.get_job_controller()

                dm.close()

                # 判断当前存储策略是否有辅助拷贝未完成
                auxcopy_completed = True
                for job in jobs_controller:
                    if job['storagePolicy'] == data_sp and job['operation'] == "Aux Copy":
                        auxcopy_completed = False
                        break
                # 假设未恢复成功
                # auxcopy_status = 'ERROR'
                print('当前备份记录对应的辅助拷贝状态 %s' % auxcopy_completed)
                if not auxcopy_completed:
                    # 找到成功的辅助拷贝，开始时间在辅助拷贝前的、值对应上的主拷贝备份时间点(最终转化UTC)
                    for auxcopy in auxcopys:
                        if auxcopy['storagepolicy'] == data_sp and auxcopy['jobstatus'] in ["Completed", "Success"]:
                            bytesxferred = auxcopy['bytesxferred']

                            end_tag = False
                            for orcl_copy in oraclecopys:
                                try:
                                    orcl_copy_starttime = datetime.datetime.strptime(orcl_copy['StartTime'],
                                                                                     "%Y-%m-%d %H:%M:%S")
                                    aux_copy_starttime = datetime.datetime.strptime(auxcopy['startdate'],
                                                                                    "%Y-%m-%d %H:%M:%S")
                                    if orcl_copy[
                                        'numbytesuncomp'] == bytesxferred and orcl_copy_starttime < aux_copy_starttime and \
                                            orcl_copy['subclient'] == "default":
                                        # 获取enddate,转化时间
                                        curSCN = orcl_copy['cur_SCN']
                                        end_tag = True
                                        break
                                except Exception as e:
                                    print(e)
                            if end_tag:
                                break

            dm.close()
            # print('Rac %s' % curSCN)
            oraRestoreOperator = {"curSCN": curSCN, "browseJobId": None, "data_path": data_path,
                                  "copy_priority": copy_priority, "restoreTime": restoreTime}
            # print("> %s > %s, %s, %s" % (oraRestoreOperator, sourceClient, destClient, instance))

            cvToken = CV_RestApi_Token()
            cvToken.login(commvault_credit)
            cvAPI = CV_API(cvToken)
            if agent.upper() == "ORACLE DATABASE":
                if cvAPI.restoreOracleBackupset(sourceClient, destClient, instance, oraRestoreOperator):
                    return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
                else:
                    return HttpResponse("恢复任务启动失败。" + cvAPI.msg)
            elif agent.upper() == "ORACLE RAC":
                oraRestoreOperator["browseJobId"] = browseJobId
                if cvAPI.restoreOracleRacBackupset(sourceClient, destClient, instance, oraRestoreOperator):
                    return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
                else:
                    return HttpResponse("恢复任务启动失败。" + cvAPI.msg)
            else:
                return HttpResponse("无当前模块，恢复任务启动失败。")
    else:
        return HttpResponse("恢复任务启动失败。")


@login_required
def monitor(request):
    global funlist
    # 最新操作
    alltask = []

    rows = []
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = """select t.starttime, t.content, t.type, t.state, t.logtype, p.name, p.color from faconstor_processtask as t left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where r.state!='9' order by t.starttime desc;"""
            cursor.execute(sql)
            rows = cursor.fetchall()
    finally:
        connection.close()

    # cursor = connection.cursor()
    # cursor.execute("""
    # select t.starttime, t.content, t.type, t.state, t.logtype, p.name, p.color from faconstor_processtask as t left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where r.state!='9' order by t.starttime desc;
    # """)
    # rows = cursor.fetchall()

    if len(rows) > 0:
        for task in rows:
            time = task[0]
            content = task[1]
            task_type = task[2]
            task_state = task[3]
            task_logtype = task[4]
            process_name = task[5]
            process_color = task[6]

            # 图标与颜色
            current_icon, current_color = custom_c_color(task_type, task_state, task_logtype)

            time = custom_time(time)

            alltask.append(
                {"content": content, "time": time, "process_name": process_name, "task_color": current_color,
                 "task_icon": current_icon, "process_color": process_color})
            if len(alltask) >= 50:
                break
    # 成功率，恢复次数，平均RTO，最新切换
    all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="STOP"))
    successful_processruns = ProcessRun.objects.filter(state="DONE")
    processrun_times_obj = ProcessRun.objects.exclude(state__in=["RUN", "REJECT"]).exclude(state="9")

    success_rate = "%.0f" % (len(successful_processruns) / len(
        all_processrun_objs) * 100) if all_processrun_objs and successful_processruns else 0

    last_processrun_time = successful_processruns.last().starttime if successful_processruns else ""
    all_processruns = len(processrun_times_obj) if processrun_times_obj else 0

    current_processruns = ProcessRun.objects.exclude(state__in=["DONE", "STOP", "REJECT"]).exclude(
        state="9").select_related("process")
    curren_processrun_info_list = []
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
        "": "",
    }

    process_rate = "0"
    if current_processruns:
        for current_processrun in current_processruns:
            current_processrun_dict = {}
            start_time_strftime = ""
            current_delta_time = ""
            current_step_name = ""
            current_process_name = ""
            current_step_index = ""
            all_steps = []
            group_name = ""
            users = ""
            process_id = current_processrun.process_id
            current_process_name = current_processrun.process.name
            start_time = current_processrun.starttime.replace(tzinfo=None)
            start_time_strftime = start_time.strftime('%Y-%m-%d %H:%M:%S')
            current_time = datetime.datetime.now()
            current_delta_time = (current_time - start_time).total_seconds()
            m, s = divmod(current_delta_time, 60)
            h, m = divmod(m, 60)
            current_delta_time = "%d时%02d分%02d秒" % (h, m, s)

            current_processrun_id = current_processrun.id

            # 进程url
            processrun_url = current_processrun.process.url + "/" + str(current_processrun_id)

            # 当前系统任务
            current_process_task_info = get_c_process_run_tasks(current_processrun.id)

            current_processrun_dict["current_process_run_state"] = state_dict[
                "{0}".format(current_processrun.state)]
            current_processrun_dict["current_process_task_info"] = current_process_task_info
            current_processrun_dict["current_processrun_dict"] = current_processrun_dict
            current_processrun_dict["start_time_strftime"] = start_time_strftime
            current_processrun_dict["current_delta_time"] = current_delta_time
            current_processrun_dict["current_process_name"] = current_process_name
            current_processrun_dict["current_step_index"] = current_step_index
            current_processrun_dict["all_steps"] = all_steps
            current_processrun_dict["process_rate"] = process_rate
            current_processrun_dict["current_step_name"] = current_step_name
            current_processrun_dict["group_name"] = group_name
            current_processrun_dict["users"] = users
            current_processrun_dict["processrun_url"] = processrun_url
            current_processrun_dict["processrun_id"] = current_processrun.id

            curren_processrun_info_list.append(current_processrun_dict)

    ##################################
    # 今日演练：                      #
    #   今天演练过的系统个数/总系统数  #
    ##################################
    today_process_run_length = 0
    today_date = datetime.datetime.now().date()
    pre_client = ""
    for processrun_obj in all_processrun_objs:
        if today_date == processrun_obj.starttime.date():
            if pre_client == processrun_obj.origin:
                continue
            today_process_run_length += 1

            pre_client = processrun_obj.origin

    all_process = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))

    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    # 右上角消息任务
    return render(request, "monitor.html",
                  {'username': request.user.userinfo.fullname, "alltask": alltask, "homepage": True,
                   "success_rate": success_rate, "utils_manage": utils_manage,
                   "all_processruns": all_processruns, "last_processrun_time": last_processrun_time,
                   "curren_processrun_info_list": curren_processrun_info_list,
                   "today_process_run_length": today_process_run_length, "all_process": all_process})


@login_required
def get_monitor_data(request):
    drill_day = []

    # 最近7日演练次数
    drill_times = []
    drill_rto = []
    for i in range(0, 7)[::-1]:
        today_datetime = datetime.datetime.now()
        if i == 0:
            pass
        else:
            today_datetime = today_datetime - datetime.timedelta(days=i)
        today_drills = ProcessRun.objects.exclude(state__in=["RUN", "REJECT", "9", "STOP"]).filter(
            starttime__startswith=today_datetime.date())
        drill_day.append("{0:%m-%d}".format(today_datetime.date()))
        drill_times.append(len(today_drills))

        # 平均RTO趋势
        cur_client_succeed_process = ProcessRun.objects.filter(state="DONE").filter(
            starttime__startswith=today_datetime.date())

        if cur_client_succeed_process:
            rto_sum_seconds = 0

            for processrun in cur_client_succeed_process:
                ########################################################
                # 构造出正确顺序的父级步骤RTO，                         #
                # 最后一个步骤rto_count_in="0"，记录endtime为rtoendtime #
                ########################################################
                delta_time = get_process_run_rto(processrun)
                rto_sum_seconds += delta_time

            rto = "%.2f" % (rto_sum_seconds / 60)

            drill_rto.append(rto)
        else:
            drill_rto.append(0)

    week_drill = {
        "drill_day": drill_day,
        "drill_times": drill_times
    }

    avgRTO = {
        "drill_day": drill_day,
        "drill_rto": drill_rto
    }

    # 系统演练次数TOP5
    all_process = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))
    drill_name = []
    drill_time = []
    for process in all_process:
        process_runs = process.processrun_set.exclude(state__in=["RUN", "REJECT", "9", "STOP"])
        cur_drill_time = len(process_runs)

        if drill_time:
            for dt in drill_time:
                dt_index = drill_time.index(dt)
                if cur_drill_time > dt:
                    drill_name.insert(dt_index, process.name)
                    drill_time.insert(dt_index, cur_drill_time)
                    break
            else:
                drill_name.append(process.name)
                drill_time.append(cur_drill_time)
        else:
            drill_name.append(process.name)
            drill_time.append(cur_drill_time)

    drill_top_time = {
        "drill_name": drill_name[:5][::-1] if len(drill_name[::-1]) > 5 else drill_name,
        "drill_time": drill_time[:5][::-1] if len(drill_time[::-1]) > 5 else drill_time
    }
    # print(drill_top_time)
    # 演练成功率
    all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="ERROR") | Q(state='STOP'))
    successful_processruns = ProcessRun.objects.filter(state="DONE")

    success_rate = "%.0f" % (len(successful_processruns) / len(
        all_processrun_objs) * 100) if all_processrun_objs and successful_processruns else 0
    drill_rate = [success_rate, 100 - int(success_rate)]

    # 演练日志
    task_list = []
    all_process_tasks = ProcessTask.objects.filter(logtype__in=["ERROR", "STOP", "END", "START"]).order_by(
        "-starttime").select_related("processrun", "processrun__process")
    for num, process_task in enumerate(all_process_tasks):
        if num == 50:
            break
        process_name = ""
        try:
            process_name = process_task.processrun.process.name
        except:
            pass

        task_list.append({
            "process_name": process_name,
            "start_time": "{0: %Y-%m-%d %H:%M:%S}".format(process_task.starttime) if process_task.starttime else "",
            "content": process_task.content
        })
    # 今日作业
    running_job, success_job, error_job, stop_job = 0, 0, 0, 0
    all_processes = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type=""))
    has_run_process = 0
    for process in all_processes:
        process_run = process.processrun_set.exclude(state__in=["9", "REJECT"]).filter(
            starttime__startswith=datetime.datetime.now().date())
        if process_run.exists():
            has_run_process += 1

            # 运行中
            if process_run.last().state == "RUN":
                running_job += 1

            # 成功流程，最后一个流程成功
            if process_run.last().state == "DONE":
                success_job += 1

            # 失败流程：最后一次失败
            if process_run.last().state == "ERROR":
                error_job += 1

            # 终止流程
            if process_run.last().state == "STOP":
                stop_job += 1

    not_running = 0
    try:
        # 未启动
        not_running = len(all_processes) - running_job - success_job - error_job - stop_job
    except:
        pass

    # 演练监控
    drill_monitor = []

    for process in all_processes:
        today_process_run = process.processrun_set.exclude(state__in=["9", "REJECT"]).filter(
            starttime__startswith=datetime.datetime.now().date())

        if today_process_run:
            today_process_run = today_process_run.last()
            done_step_run = today_process_run.steprun_set.filter(state="DONE")
            if done_step_run.exists():
                done_num = len(done_step_run)
            else:
                done_num = 0

            # 构造展示步骤
            process_rate = "%02d" % (done_num / len(today_process_run.steprun_set.all()) * 100)

            # 策略时间
            cur_schedule = ""
            try:
                process_schedule = ProcessSchedule.objects.filter(process=process).exclude(state="9")
                if process_schedule.exists():
                    cur_schedule_hour = process_schedule[0].dj_periodictask.crontab.hour
                    cur_schedule_minute = process_schedule[0].dj_periodictask.crontab.minute
                    cur_schedule = "{0}:{1}".format(cur_schedule_hour, cur_schedule_minute)
            except:
                pass

            drill_monitor.append({
                "process_name": process.name,
                "state": today_process_run.state,
                "schedule_time": cur_schedule,
                "start_time": "{0:%Y-%m-%d %H:%M:%S}".format(
                    today_process_run.starttime) if today_process_run.starttime else "",
                "end_time": "{0:%Y-%m-%d %H:%M:%S}".format(
                    today_process_run.endtime) if today_process_run.endtime else "",
                "percent": "{0}%".format((int(process_rate)))
            })
        else:
            # 策略时间
            cur_schedule = ""
            try:
                process_schedule = ProcessSchedule.objects.filter(process=process).exclude(state="9")
                if process_schedule.exists():
                    cur_schedule_hour = process_schedule[0].dj_periodictask.crontab.hour
                    cur_schedule_minute = process_schedule[0].dj_periodictask.crontab.minute
                    cur_schedule = "{0}:{1}".format(cur_schedule_hour, cur_schedule_minute)
            except:
                pass
            drill_monitor.append({
                "process_name": process.name,
                "state": "未演练",
                "schedule_time": cur_schedule,
                "start_time": "",
                "end_time": "",
                "percent": "0%"
            })

    # 待处理异常
    error_processrun_list = []
    error_processrun = ProcessRun.objects.filter(state="ERROR").select_related("process").order_by("-starttime")
    for epr in error_processrun:
        error_processrun_list.append({
            "process_name": epr.process.name,
            "start_time": "{0:%Y-%m-%d %H:%M:%S}".format(epr.starttime) if epr.starttime else "",
            "processrun_url": "/falconstor/{processrun_id}/".format(processrun_id=epr.id)
        })
    return JsonResponse({
        "week_drill": week_drill,
        "avgRTO": avgRTO,
        "drill_top_time": drill_top_time,
        "drill_rate": drill_rate,
        "drill_monitor": drill_monitor,
        "task_list": task_list,
        "today_job": {
            "running_job": running_job,
            "success_job": success_job,
            "error_job": error_job,
            "not_running": not_running
        },
        "error_processrun": error_processrun_list
    })


@login_required
def get_clients_status(request):
    utils_id = request.POST.get("utils_id", "")
    try:
        utils_id = int(utils_id)
        utils_manage = UtilsManage.objects.get(id=utils_id)
    except:
        return JsonResponse({
            "clients_status": {
                "service_status": "无",
                "net_status": "无",
                "all_clients": 0,
                "whole_backup_list": []
            }
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        # 客户端状态
        dm = SQLApi.CVApi(sqlserver_credit)

        if dm.msg == "链接数据库失败。":
            service_status = "中断"
            net_status = "中断"
        else:
            service_status = "正常"
            net_status = "正常"

        # 客户端列表
        client_list = Origin.objects.exclude(state=9).values_list("client_name")
        client_name_list = [client_name[0] for client_name in client_list]
        # 报警客户端
        whole_backup_list = dm.get_backup_status(client_name_list)
        dm.close()
        return JsonResponse({
            "clients_status": {
                "service_status": service_status,
                "net_status": net_status,
                "all_clients": len(client_list),
                "whole_backup_list": whole_backup_list
            }
        })


def get_process_run_rto(processrun):
    ########################################################
    # 构造出正确顺序的父级步骤RTO，                         #
    # 最后一个步骤rto_count_in="0"，记录endtime为rtoendtime #
    ########################################################
    # cur_process = processrun.process
    #
    # # 正确顺序的父级Step
    # all_pnode_steps = cur_process.step_set.exclude(state="9").filter(pnode_id=None).order_by("sort")
    #
    # correct_step_id_list = []
    # if all_pnode_steps:
    #     for pnode_step in all_pnode_steps:
    #         correct_step_id_list.append(pnode_step)
    # else:
    #     raise Http404()
    #
    # # 正确顺序的父级StepRun
    # correct_step_run_list = []
    #
    # for pnode_step in correct_step_id_list:
    #     current_step_run = pnode_step.steprun_set.filter(processrun_id=processrun.id)
    #     if current_step_run.exists():
    #         current_step_run = current_step_run[0]
    #         correct_step_run_list.append(current_step_run)
    # starttime = processrun.starttime
    # rtoendtime = processrun.starttime
    # if correct_step_run_list:
    #     for c_step_run in reversed(correct_step_run_list):
    #         if c_step_run.step.rto_count_in == "1":
    #             rtoendtime = c_step_run.endtime
    #             break
    # delta_time = 0
    # if rtoendtime:
    #     delta_time = (rtoendtime - starttime).total_seconds()

    delta_time = processrun.rto
    return delta_time
