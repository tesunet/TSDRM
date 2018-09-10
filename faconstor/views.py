# coding:utf-8

from django.shortcuts import render
from django.contrib import auth
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from faconstor.models import *
from django.http import StreamingHttpResponse
import time
import datetime
from django.db.models import Q
import sys
import os
import json
import random
from django.core.mail import send_mail
from TSDRM import settings
import uuid
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
from faconstor.tasks import *
from django.db.models import Count
from django.db.models import Sum, Max
from django.db import connection
import xlrd, xlwt
import pythoncom
import pymssql
from lxml import etree
from django.forms.models import model_to_dict
import re

pythoncom.CoInitialize()
import wmi

funlist = []

info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
        "lastlogin": 0}


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
                                   "isselected": returnfuns["isselected"], "child": returnfuns["fun"]})
                if returnfuns["isselected"]:
                    pisselected = returnfuns["isselected"]
    return {"fun": mychildfun, "isselected": pisselected}


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
        # 左上角消息下拉菜单
        mygroup = []
        userinfo = request.user.userinfo
        guoups = userinfo.group.all()
        pop = False
        if len(guoups) > 0:
            for curguoup in guoups:
                mygroup.append(str(curguoup.id))
        allprosstasks = ProcessTask.objects.filter(
            Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(state="0").order_by(
            "-starttime").all()
        if len(allprosstasks) > 0:
            for task in allprosstasks:
                send_time = task.starttime
                process_name = task.processrun.process.name
                process_run_reason = task.processrun.run_reason
                task_id = task.id

                task_nums = len(allprosstasks)
                process_name = task.processrun.process.name
                process_color = task.processrun.process.color
                process_url = task.processrun.process.url + "/" + str(task.processrun.id)
                time = task.starttime
                time = time.replace(tzinfo=None)
                timenow = datetime.datetime.now()
                days = int((timenow - time).days)
                hours = int((timenow - time).seconds / 3600)

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
                message_task.append(
                    {"content": task.content, "time": time, "process_name": process_name,
                     "task_color": current_color.strip(),
                     "task_icon": current_icon, "process_color": process_color.strip(), "process_url": process_url,
                     "pop": pop, "task_id": task_id, "process_name": process_name, "send_time": send_time,
                     "process_run_reason": process_run_reason, "group_name": guoups[0].name})
    return {"pagefuns": pagefuns, "curfun": mycurfun, "message_task": message_task, "task_nums": task_nums}


def test(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        return render(request, 'test.html',
                      {'username': request.user.userinfo.fullname, "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def index(request, funid):
    if request.user.is_authenticated():
        global funlist
        funlist = []
        if request.user.is_superuser == 1:
            allfunlist = Fun.objects.all()
            for fun in allfunlist:
                funlist.append(fun)
        else:
            cursor = connection.cursor()
            cursor.execute(
                "select cloud_fun.id from cloud_group,cloud_fun,cloud_userinfo,cloud_userinfo_group,cloud_group_fun "
                "where cloud_group.id=cloud_userinfo_group.group_id and cloud_group.id=cloud_group_fun.group_id and "
                "cloud_group_fun.fun_id=cloud_fun.id and cloud_userinfo.id=cloud_userinfo_group.userinfo_id and userinfo_id= "
                + str(request.user.userinfo.id) + " order by cloud_fun.sort"
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

        alltask = []
        mygroup = []
        userinfo = request.user.userinfo
        guoups = userinfo.group.all()
        if len(guoups) > 0:
            for curguoup in guoups:
                mygroup.append(str(curguoup.id))
        allprosstasks = ProcessTask.objects.filter(
            Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(
            Q(state="0") | Q(state="1")).order_by(
            "-starttime").all()
        if len(allprosstasks) > 0:
            for task in allprosstasks:
                process_name = task.processrun.process.name
                process_color = task.processrun.process.color

                process_type = task.type
                time = ""
                time = task.starttime
                time = time.replace(tzinfo=None)
                timenow = datetime.datetime.now()
                days = int((timenow - time).days)
                hours = int((timenow - time).seconds / 3600)
                task_id = task.id

                # 图标与颜色
                if task.type == "ERROR":
                    current_icon = "fa fa-exclamation-triangle"
                    if task.state == "0":
                        current_color = "label-danger"
                    if task.state == "1":
                        current_color = "label-default"
                elif task.type == "SIGN":
                    current_icon = "fa fa-user"
                    if task.state == "0":
                        current_color = "label-warning"
                    if task.state == "1":
                        current_color = "label-info"
                elif task.type == "RUN":
                    current_icon = "fa fa-bell-o"
                    if task.state == "0":
                        current_color = "label-warning"
                    if task.state == "1":
                        current_color = "label-info"
                else:
                    current_color = "label-success"
                    if task.logtype == "START":
                        current_icon = "fa fa-power-off"
                    elif task.logtype == "START":
                        current_icon = "fa fa-power-off"
                    elif task.logtype == "STEP":
                        current_icon = "fa fa-cog"
                    elif task.logtype == "SCRIPT":
                        current_icon = "fa fa-cog"
                    elif task.logtype == "STOP":
                        current_icon = "fa fa-stop"
                    elif task.logtype == "CONTINUE":
                        current_icon = "fa fa-play"
                    elif task.logtype == "IGNORE":
                        current_icon = "fa fa-share"
                    elif task.logtype == "START":
                        current_icon = "fa fa-power-off"
                    elif task.logtype == "END":
                        current_icon = "fa fa-lock"
                    else:
                        current_icon = "fa fa-info-circle"

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

                alltask.append(
                    {"content": task.content, "time": time, "process_name": process_name, "task_color": current_color,
                     "task_icon": current_icon, "process_color": process_color})

        # 成功率，恢复次数，平均RTO，最新切换
        all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="STOP"))
        successful_processruns = ProcessRun.objects.filter(state="DONE")
        processrun_times_obj = ProcessRun.objects.exclude(state="RUN")

        success_rate = "%.0f" % (len(successful_processruns) / len(
            all_processrun_objs) * 100) if all_processrun_objs and successful_processruns else 0
        last_processrun_time = successful_processruns.last().starttime if successful_processruns else ""
        all_processruns = len(processrun_times_obj) if processrun_times_obj else 0
        if successful_processruns:
            all_rto = 0
            for processrun in successful_processruns:
                end_time = processrun.endtime
                start_time = processrun.starttime
                if end_time and start_time:
                    delta_time = (end_time - start_time)
                    rto = delta_time.total_seconds()
                    all_rto += rto

            m, s = divmod(all_rto, 60)
            h, m = divmod(m, 60)
            average_rto = "%d时%02d分%02d秒" % (h, m, s)

        else:
            average_rto = "0时0分0秒"

        # 正在切换:start_time, delta_time, current_step, current_operator， current_process_name, all_steps
        current_processruns = ProcessRun.objects.filter(state="RUN")
        curren_processrun_info_list = []
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
                all_stepruns = StepRun.objects.filter(processrun_id=current_processrun_id)


                # 没有run的情况下，
                try:
                    # 如果步骤小于3个
                    if len(all_stepruns) >= 3:
                        all_stepruns_display = all_stepruns[:3]
                    else:
                        all_stepruns_display = all_stepruns[:len(all_stepruns)]

                    if all_stepruns[0].state == "RUN":
                        current_step_index = 1
                        for num, steprun in enumerate(all_stepruns_display):
                            if num == 0:
                                current_step_name = steprun.step.name
                                # 负责角色
                                group_id = steprun.step.group
                                if group_id:
                                    group_name = Group.objects.filter(id=int(group_id))[0].name
                                    users_from_group = Group.objects.filter(id=int(group_id))[
                                        0].userinfo_set.all().values_list(
                                        "fullname")
                                    users = ""
                                    for num, user in enumerate(users_from_group):
                                        users += user[0] + "、"
                                    users = "({0})".format(users[:-1])
                            all_steps.append(steprun.step.name)
                    elif all_stepruns[len(all_stepruns) - 1].state == "RUN" and all_stepruns[
                        len(all_stepruns) - 2].state == "DONE":
                        current_step_index = len(all_stepruns)
                        for num, steprun in enumerate(all_stepruns[len(all_stepruns) - len(all_stepruns_display):]):
                            if num == len(all_stepruns[len(all_stepruns) - 3:]) - 1:
                                current_step_name = steprun.step.name
                                # 负责角色
                                group_id = steprun.step.group
                                if group_id:
                                    group_name = Group.objects.filter(id=int(group_id))[0].name
                                    users_from_group = Group.objects.filter(id=int(group_id))[
                                        0].userinfo_set.all().values_list(
                                        "fullname")
                                    users = ""
                                    for num, user in enumerate(users_from_group):
                                        users += user[0] + "、"
                                    users = "({0})".format(users[:-1])
                            all_steps.append(steprun.step.name)
                    else:
                        currentrun_step = all_stepruns.filter(state="RUN").first()
                        current_step_name = currentrun_step.step.name

                        # 负责角色
                        group_id = currentrun_step.step.group
                        if group_id:
                            group_name = Group.objects.filter(id=int(group_id))[0].name
                            users_from_group = Group.objects.filter(id=int(group_id))[
                                0].userinfo_set.all().values_list(
                                "fullname")
                            users = ""
                            for num, user in enumerate(users_from_group):
                                users += user[0] + "、"
                            users = "({0})".format(users[:-1])

                        # 前一个后一个名称
                        current_num = ""
                        for num, steprun in enumerate(all_stepruns):
                            if steprun.state == "RUN":
                                current_num = num
                                break
                        for num, steprun in enumerate(all_stepruns):
                            if num == current_num - 1 or num == current_num + 1 or num == current_num:
                                all_steps.append(steprun.step.name)
                        current_step_index = current_num + 1
                except:
                    pass

                total_steps = Step.objects.exclude(state="9").filter(process_id=process_id).values_list("name")
                # 总体进度
                process_rate = "%02d" % (current_step_index / len(total_steps) * 100) if current_step_index else ""

                # 进程url
                processrun_url = current_processrun.process.url + "/" + str(current_processrun_id)

                # 当前系统任务
                current_process_task_info = []

                current_process_tasks = ProcessTask.objects.filter(
                    Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(
                    Q(state="0") | Q(state="1")).filter(processrun_id=current_processrun.id).order_by(
                    "-starttime").all()
                if len(current_process_tasks) > 0:
                    for task in current_process_tasks:
                        time = ""
                        time = task.starttime
                        time = time.replace(tzinfo=None)
                        timenow = datetime.datetime.now()
                        days = int((timenow - time).days)
                        hours = int((timenow - time).seconds / 3600)

                        # 图标与颜色
                        if task.type == "ERROR":
                            current_icon = "fa fa-exclamation-triangle"
                            if task.state == "0":
                                current_color = "label-danger"
                            if task.state == "1":
                                current_color = "label-default"
                        elif task.type == "SIGN":
                            current_icon = "fa fa-user"
                            if task.state == "0":
                                current_color = "label-warning"
                            if task.state == "1":
                                current_color = "label-info"
                        elif task.type == "RUN":
                            current_icon = "fa fa-bell-o"
                            if task.state == "0":
                                current_color = "label-warning"
                            if task.state == "1":
                                current_color = "label-info"
                        else:
                            current_color = "label-success"
                            if task.logtype == "START":
                                current_icon = "fa fa-power-off"
                            elif task.logtype == "START":
                                current_icon = "fa fa-power-off"
                            elif task.logtype == "STEP":
                                current_icon = "fa fa-cog"
                            elif task.logtype == "SCRIPT":
                                current_icon = "fa fa-cog"
                            elif task.logtype == "STOP":
                                current_icon = "fa fa-stop"
                            elif task.logtype == "CONTINUE":
                                current_icon = "fa fa-play"
                            elif task.logtype == "IGNORE":
                                current_icon = "fa fa-share"
                            elif task.logtype == "START":
                                current_icon = "fa fa-power-off"
                            elif task.logtype == "END":
                                current_icon = "fa fa-lock"
                            else:
                                current_icon = "fa fa-info-circle"

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

                        current_process_task_info.append(
                            {"content": task.content, "time": time, "task_color": current_color,
                             "task_icon": current_icon})

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

                curren_processrun_info_list.append(current_processrun_dict)

        # 系统切换成功率
        all_processes = Process.objects.exclude(state="9").filter(type="falconstor")
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

        # 左上角消息任务
        return render(request, "index.html",
                      {'username': request.user.userinfo.fullname, "alltask": alltask, "homepage": True,
                       "pagefuns": getpagefuns(funid, request), "success_rate": success_rate,
                       "all_processruns": all_processruns,
                       "last_processrun_time": last_processrun_time, "average_rto": average_rto,
                       "curren_processrun_info_list": curren_processrun_info_list,
                       "process_success_rate_list": process_success_rate_list})
    else:
        return HttpResponseRedirect("/login")


def get_process_rto(request):
    if request.user.is_authenticated():
        # 不同流程最近的12次切换RTO
        all_processes = Process.objects.exclude(state="9").filter(type="falconstor")
        process_rto_list = []
        if all_processes:
            for process in all_processes:
                process_name = process.name
                processrun_rto_obj_list = process.processrun_set.filter(state="DONE")
                current_rto_list = []
                for processrun_rto_obj in processrun_rto_obj_list:
                    start_time = processrun_rto_obj.starttime
                    end_time = processrun_rto_obj.endtime
                    delta_time = (end_time - start_time).total_seconds() if start_time and end_time else 0
                    current_rto = int("%.2d" % (delta_time / 60))
                    current_rto_list.append(current_rto)
                process_dict = {
                    "process_name": process_name,
                    "current_rto_list": current_rto_list,
                    "color": process.color
                }
                process_rto_list.append(process_dict)

        return JsonResponse({"data": process_rto_list if len(process_rto_list) <= 12 else process_rto_list[-12:]})


def get_daily_processrun(request):
    if request.user.is_authenticated():
        all_processrun_objs = ProcessRun.objects.filter(Q(state="DONE") | Q(state="STOP"))
        process_success_rate_list = []
        if all_processrun_objs:
            for process_run in all_processrun_objs:
                process_name = process_run.process.name
                start_time = process_run.starttime
                end_time = process_run.endtime
                process_color = process_run.process.color
                process_run_id = process_run.id
                # 进程url
                processrun_url = process_run.process.url + "/" + str(process_run.id)

                process_run_dict = {
                    "process_name": process_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "process_color": process_color,
                    "process_run_id": process_run_id,
                    "url": processrun_url,
                }
                process_success_rate_list.append(process_run_dict)
        return JsonResponse({"data": process_success_rate_list})


def login(request):
    auth.logout(request)
    try:
        del request.session['ispuser']
        del request.session['isadmin']
    except KeyError:
        pass
    return render(request, 'login.html', context_instance=RequestContext(request))


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


def password(request):
    if request.user.is_authenticated():
        return render(request, 'password.html', {"myusername": request.user.username})
    else:
        return HttpResponseRedirect("/login")


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


def function(request, funid):
    if request.user.is_authenticated():
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
    else:
        return HttpResponseRedirect("/login")


def fundel(request):
    if request.user.is_authenticated():
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


def funmove(request):
    if request.user.is_authenticated():
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


def organization(request, funid):
    if request.user.is_authenticated():
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
                           "selectgroup": selectgroup, "mytype": mytype,
                           "remark": remark, "title": title, "mytype": mytype, "hiddenuser": hiddenuser,
                           "hiddenorg": hiddenorg,
                           "newpassword": newpassword, "editpassword": editpassword, "hiddendiv": hiddendiv
                              , "treedata": treedata, "pagefuns": getpagefuns(funid, request=request)})

        except:
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


def orgdel(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            userinfo = UserInfo.objects.get(id=id)
            userinfo.state = "9"
            userinfo.save()

            if userinfo.type == "user":
                user = userinfo.user
                user.is_active = 0
                user.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def orgmove(request):
    if request.user.is_authenticated():
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
            userinfos = UserInfo.objects.filter(pnode=puserinfo).filter(sort__gte=sort).exclude(id=id)

            myuserinfo = UserInfo.objects.get(id=id)
            if puserinfo.type == "user":
                return HttpResponse("类型")
            else:
                usersame = UserInfo.objects.filter(pnode=puserinfo).filter(fullname=myuserinfo.fullname).exclude(id=id)
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


def orgpassword(request):
    if request.user.is_authenticated():
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


def group(request, funid):
    if request.user.is_authenticated():
        try:
            allgroup = Group.objects.all().exclude(state="9")

            return render(request, 'group.html',
                          {'username': request.user.userinfo.fullname,
                           "allgroup": allgroup, "pagefuns": getpagefuns(funid, request)})
        except:
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


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


def groupsavefuntree(request):
    if 'id' in request.POST:
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


def script(request, funid):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        if request.method == 'POST':
            my_file = request.FILES.get("myfile", None)  # 获取上传的文件，如果没有文件，则默认为None
            if not my_file:
                errors.append("请选择要导入的文件。")
            else:
                filetype = my_file.name.split(".")[-1]
                if filetype == "xls" or filetype == "xlsx":
                    myfilepath = os.path.join(os.path.join(os.path.dirname(__file__), "upload\\temp"), my_file.name)
                    destination = open(myfilepath, 'wb+')
                    for chunk in my_file.chunks():  # 分块写入文件
                        destination.write(chunk)
                    destination.close()

                    data = xlrd.open_workbook(myfilepath)
                    sheet = data.sheets()[0]
                    rows = sheet.nrows
                    errors.append("导入成功。")
                    for i in range(rows):
                        if i > 0:
                            try:
                                allscript = Script.objects.filter(code=sheet.cell(i, 0).value).exclude(
                                    state="9").filter(step_id=None)
                                if (len(allscript) > 0):
                                    errors.append(sheet.cell(i, 0).value + ":已存在。")
                                else:
                                    ncols = sheet.ncols
                                    scriptsave = Script()
                                    scriptsave.code = sheet.cell(i, 0).value
                                    scriptsave.ip = sheet.cell(i, 1).value
                                    scriptsave.port = sheet.cell(i, 2).value
                                    scriptsave.type = sheet.cell(i, 3).value
                                    scriptsave.runtype = sheet.cell(i, 4).value
                                    scriptsave.username = sheet.cell(i, 5).value
                                    scriptsave.password = sheet.cell(i, 6).value
                                    scriptsave.filename = sheet.cell(i, 7).value
                                    scriptsave.paramtype = sheet.cell(i, 8).value
                                    scriptsave.param = sheet.cell(i, 9).value
                                    scriptsave.scriptpath = sheet.cell(i, 10).value
                                    scriptsave.runpath = sheet.cell(i, 11).value
                                    scriptsave.maxtime = int(sheet.cell(i, 12).value)
                                    scriptsave.time = int(sheet.cell(i, 13).value)
                                    scriptsave.save()
                            except:
                                errors.append(sheet.cell(i, 0).value + ":数据存在问题，已剔除。")
                    os.remove(myfilepath)
                else:
                    errors.append("只能上传xls和xlsx文件，请选择正确的文件类型。")
        return render(request, 'script.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def scriptdata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allscript = Script.objects.exclude(state="9").filter(step_id=None)
        if (len(allscript) > 0):
            for script in allscript:
                result.append(
                    {"id": script.id, "code": script.code, "name": script.name, "ip": script.ip, "port": script.port,
                     "type": script.type, "runtype": script.runtype, "username": script.username,
                     "password": script.password, "filename": script.filename, "paramtype": script.paramtype,
                     "param": script.param, "scriptpath": script.scriptpath, "runpath": script.runpath,
                     "maxtime": script.maxtime, "time": script.time})
        return HttpResponse(json.dumps({"data": result}))


def scriptdel(request):
    """
    当删除脚本管理中的脚本的同时，需要删除预案中绑定的脚本；
    :param request:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
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


def scriptsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            ip = request.POST.get('ip', '')
            # port = request.POST.get('port', '')
            type = request.POST.get('type', '')
            # runtype = request.POST.get('runtype', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            filename = request.POST.get('filename', '')
            # paramtype = request.POST.get('paramtype', '')
            # param = request.POST.get('param', '')
            scriptpath = request.POST.get('scriptpath', '')
            # runpath = request.POST.get('runpath', '')
            # maxtime = request.POST.get('maxtime', '')
            # time = request.POST.get('time', '')
            try:
                id = int(id)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '脚本编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '脚本名称不能为空。'
                else:
                    if ip.strip() == '':
                        result["res"] = '主机IP不能为空。'
                    else:
                        # if port.strip() == '':
                        #     result["res"] = '端口号不能为空。'
                        # else:
                        if type.strip() == '':
                            result["res"] = '连接类型不能为空。'
                        else:
                            if username.strip() == '':
                                result["res"] = '用户名不能为空。'
                            else:
                                if password.strip() == '':
                                    result["res"] = '密码不能为空。'
                                else:
                                    if filename.strip() == '':
                                        result["res"] = '脚本文件名不能为空。'
                                    else:
                                        if scriptpath.strip() == '':
                                            result["res"] = '脚本文件路径不能为空。'
                                        else:
                                            # if runpath.strip() == '':
                                            #     result["res"] = '执行路径不能为空。'
                                            # else:
                                            #     if maxtime.strip() == '':
                                            #         result["res"] = '超时时间不能为空。'
                                            #     else:
                                            #         if time.strip() == '':
                                            #             result["res"] = '预计耗时不能为空。'
                                            #         else:
                                            if id == 0:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    state="9").filter(step_id=None)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + code + '已存在。'
                                                else:
                                                    scriptsave = Script()
                                                    scriptsave.code = code
                                                    scriptsave.name = name
                                                    scriptsave.ip = ip
                                                    # scriptsave.port = port
                                                    scriptsave.type = type
                                                    # scriptsave.runtype = runtype
                                                    scriptsave.username = username
                                                    scriptsave.password = password
                                                    scriptsave.filename = filename
                                                    # scriptsave.paramtype = paramtype
                                                    # scriptsave.param = param
                                                    scriptsave.scriptpath = scriptpath
                                                    # scriptsave.runpath = runpath
                                                    # try:
                                                    #     scriptsave.maxtime = int(maxtime)
                                                    # except:
                                                    #     pass
                                                    # try:
                                                    #     scriptsave.time = int(time)
                                                    # except:
                                                    #     pass
                                                    scriptsave.save()
                                                    result["res"] = "保存成功。"
                                                    result["data"] = scriptsave.id
                                            else:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9").filter(step_id=None)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + code + '已存在。'
                                                else:
                                                    try:
                                                        scriptsave = Script.objects.get(id=id)
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        # scriptsave.port = port
                                                        scriptsave.type = type
                                                        # scriptsave.runtype = runtype
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        # scriptsave.paramtype = paramtype
                                                        # scriptsave.param = param
                                                        scriptsave.scriptpath = scriptpath
                                                        # scriptsave.runpath = runpath
                                                        # try:
                                                        #     scriptsave.maxtime = int(maxtime)
                                                        # except:
                                                        #     pass
                                                        # try:
                                                        #     scriptsave.time = int(time)
                                                        # except:
                                                        #     pass
                                                        scriptsave.save()
                                                        result["res"] = "保存成功。"
                                                        result["data"] = scriptsave.id
                                                    except:
                                                        result["res"] = "修改失败。"
            return HttpResponse(json.dumps(result))


def scriptexport(request):
    # do something...
    if request.user.is_authenticated():
        myfilepath = os.path.join(os.path.dirname(__file__), "upload\\temp\\scriptexport.xls")
        try:
            os.remove(myfilepath)
        except:
            pass
        filename = xlwt.Workbook()
        sheet = filename.add_sheet('sheet1')
        allscript = Script.objects.exclude(state="9").filter(step_id=None)
        sheet.write(0, 0, u'脚本编号')
        sheet.write(0, 1, u'主机IP')
        sheet.write(0, 2, u'端口号')
        sheet.write(0, 3, u'连接类型')
        sheet.write(0, 4, u'运行类型')
        sheet.write(0, 5, u'用户名')
        sheet.write(0, 6, u'密码')
        sheet.write(0, 7, u'脚本文件名')
        sheet.write(0, 8, u'参数类型')
        sheet.write(0, 9, u'脚本参数')
        sheet.write(0, 10, u'脚本文件路径')
        sheet.write(0, 11, u'执行路径')
        sheet.write(0, 12, u'超时时间')
        sheet.write(0, 13, u'预计耗时')
        if len(allscript) > 0:
            for i in range(len(allscript)):
                sheet.write(i + 1, 0, allscript[i].code)
                sheet.write(i + 1, 1, allscript[i].ip)
                sheet.write(i + 1, 2, allscript[i].port)
                sheet.write(i + 1, 3, allscript[i].type)
                sheet.write(i + 1, 4, allscript[i].runtype)
                sheet.write(i + 1, 5, allscript[i].username)
                sheet.write(i + 1, 6, allscript[i].password)
                sheet.write(i + 1, 7, allscript[i].filename)
                sheet.write(i + 1, 8, allscript[i].paramtype)
                sheet.write(i + 1, 9, allscript[i].param)
                sheet.write(i + 1, 10, allscript[i].scriptpath)
                sheet.write(i + 1, 11, allscript[i].runpath)
                sheet.write(i + 1, 12, allscript[i].maxtime)
                sheet.write(i + 1, 13, allscript[i].time)
        filename.save(myfilepath)

        def file_iterator(file_name, chunk_size=512):
            with open(file_name, "rb") as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break

        the_file_name = "scriptexport.xls"
        response = StreamingHttpResponse(file_iterator(myfilepath))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
        return response

    else:
        return HttpResponseRedirect("/login")


def processscriptsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            processid = request.POST.get('processid', '')
            pid = request.POST.get('pid', '')
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            ip = request.POST.get('ip', '')
            # port = request.POST.get('port', '')
            type = request.POST.get('type', '')
            # runtype = request.POST.get('runtype', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            filename = request.POST.get('filename', '')
            # paramtype = request.POST.get('paramtype', '')
            # param = request.POST.get('param', '')
            scriptpath = request.POST.get('scriptpath', '')
            # runpath = request.POST.get('runpath', '')
            # maxtime = request.POST.get('maxtime', '')
            # time = request.POST.get('time', '')
            try:
                id = int(id)
                pid = int(pid)
                processid = int(processid)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '脚本编码不能为空。'
            else:
                if ip.strip() == '':
                    result["res"] = '主机IP不能为空。'
                else:
                    if name.strip() == '':
                        result["res"] = '脚本名称不能为空。'
                    else:
                        # if port.strip() == '':
                        #     result["res"] = '端口号不能为空。'
                        # else:
                        if type.strip() == '':
                            result["res"] = '连接类型不能为空。'
                        else:
                            if username.strip() == '':
                                result["res"] = '用户名不能为空。'
                            else:
                                if password.strip() == '':
                                    result["res"] = '密码不能为空。'
                                else:
                                    if filename.strip() == '':
                                        result["res"] = '脚本文件名不能为空。'
                                    else:
                                        if scriptpath.strip() == '':
                                            result["res"] = '脚本文件路径不能为空。'
                                        else:
                                            # if runpath.strip() == '':
                                            #     result["res"] = '执行路径不能为空。'
                                            # else:
                                            #     if maxtime.strip() == '':
                                            #         result["res"] = '超时时间不能为空。'
                                            #     else:
                                            #         if time.strip() == '':
                                            #             result["res"] = '预计耗时不能为空。'
                                            #         else:
                                            if id == 0:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    state="9").filter(step_id=pid)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + code + '已存在。'
                                                else:
                                                    steplist = Step.objects.filter(process_id=processid)
                                                    if len(steplist) > 0:
                                                        scriptsave = Script()
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        # scriptsave.port = port
                                                        scriptsave.type = type
                                                        # scriptsave.runtype = runtype
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        # scriptsave.paramtype = paramtype
                                                        # scriptsave.param = param
                                                        scriptsave.scriptpath = scriptpath
                                                        # scriptsave.runpath = runpath
                                                        # try:
                                                        #     scriptsave.maxtime = int(maxtime)
                                                        # except:
                                                        #     pass
                                                        # try:
                                                        #     scriptsave.time = int(time)
                                                        # except:
                                                        #     pass
                                                        scriptsave.step_id = pid
                                                        scriptsave.save()
                                                        result["res"] = "新增成功。"
                                                        result["data"] = scriptsave.id

                                            else:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9").filter(step_id=pid)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + code + '已存在。'
                                                else:
                                                    try:
                                                        scriptsave = Script.objects.get(id=id)
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        # scriptsave.port = port
                                                        scriptsave.type = type
                                                        # scriptsave.runtype = runtype
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        # scriptsave.paramtype = paramtype
                                                        # scriptsave.param = param
                                                        scriptsave.scriptpath = scriptpath
                                                        # scriptsave.runpath = runpath
                                                        # try:
                                                        #     scriptsave.maxtime = int(maxtime)
                                                        # except:
                                                        #     pass
                                                        # try:
                                                        #     scriptsave.time = int(time)
                                                        # except:
                                                        #     pass
                                                        scriptsave.save()
                                                        result["res"] = "修改成功。"
                                                        result["data"] = scriptsave.id
                                                    except:
                                                        result["res"] = "修改失败。"
            return HttpResponse(json.dumps(result))


def verify_items_save(request):
    if request.user.is_authenticated() and request.session['isadmin']:
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


def get_verify_items_data(request):
    if request.user.is_authenticated() and request.session['isadmin']:
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


def remove_verify_item(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        # 移除当前步骤中的脚本关联
        verify_id = request.POST.get("verify_id", "")
        try:
            current_verify_item = VerifyItems.objects.filter(id=verify_id)[0]
        except:
            pass
        else:
            current_verify_item.step_id = None
            current_verify_item.save()
        return JsonResponse({
            "status": 1
        })


def get_script_data(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            script_id = request.POST.get("script_id", "")
            allscript = Script.objects.exclude(state="9").filter(id=script_id)
            script_data = ""
            if (len(allscript) > 0):
                script_data = {"id": allscript[0].id, "code": allscript[0].code, "name": allscript[0].name,
                               "ip": allscript[0].ip, "port": allscript[0].port, "type": allscript[0].type,
                               "runtype": allscript[0].runtype, "username": allscript[0].username,
                               "password": allscript[0].password, "filename": allscript[0].filename,
                               "paramtype": allscript[0].paramtype, "param": allscript[0].param,
                               "scriptpath": allscript[0].scriptpath,
                               "runpath": allscript[0].runpath, "maxtime": allscript[0].maxtime,
                               "time": allscript[0].time}
            return HttpResponse(json.dumps(script_data))


def remove_script(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        # 移除当前步骤中的脚本关联
        script_id = request.POST.get("script_id", "")
        try:
            current_script = Script.objects.filter(id=script_id)[0]
        except:
            pass
        else:
            current_script.step_id = None
            current_script.save()
        return JsonResponse({
            "status": 1
        })


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
        print(group)
        if group == " ":
            group = None

        process_id = request.POST.get('process_id', '')
        try:
            id = int(id)
        except:
            raise Http404()
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
            step.time = time if time else None
            step.name = name
            step.process_id = process_id
            step.pnode_id = pid
            step.sort = my_sort
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
                step[0].save()
                result = "保存成功。"
            else:
                step = Step()
                step[0].name = name
                try:
                    time = int(time)
                    step[0].time = time
                except:
                    pass
                step.skip = skip
                step.approval = approval
                step.group = group
                step.save()
                result = "保存成功。"
        return HttpResponse(result)


def get_step_tree(parent, selectid):
    nodes = []
    children = parent.children.exclude(state="9").order_by("sort").all()
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = child.id
        node["children"] = get_step_tree(child, selectid)

        scripts = child.script_set.exclude(state="9")
        script_string = ""
        for script in scripts:
            id_code_plus = str(script.id) + "+" + str(script.code) + "&"
            script_string += id_code_plus

        verify_items_string = ""
        verify_items = child.verifyitems_set.exclude(state="9")
        for verify_item in verify_items:
            id_name_plus = str(verify_item.id) + "+" + str(verify_item.name) + "&"
            verify_items_string += id_name_plus

        group_name = ""
        if child.group:
            group_id = child.group
            if not group_id:
                group_id = None
            group_name = Group.objects.filter(id=group_id)[0].name

        all_groups = Group.objects.exclude(state="9")
        group_string = " " + "+" + " -------------- " + "&"
        for group in all_groups:
            id_name_plus = str(group.id) + "+" + str(group.name) + "&"
            group_string += id_name_plus

        node["data"] = {"time": child.time, "approval": child.approval, "skip": child.skip, "group_name": group_name,
                        "group": child.group, "scripts": script_string, "allgroups": group_string,
                        "verifyitems": verify_items_string}
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


def custom_step_tree(request):
    if request.user.is_authenticated():
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
            return Http404()
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
                scripts = rootnode.script_set.exclude(state="9")
                script_string = ""
                for script in scripts:
                    id_code_plus = str(script.id) + "+" + str(script.code) + "&"
                    script_string += id_code_plus

                verify_items_string = ""
                verify_items = rootnode.verifyitems_set.exclude(state="9")
                for verify_item in verify_items:
                    id_name_plus = str(verify_item.id) + "+" + str(verify_item.name) + "&"
                    verify_items_string += id_name_plus
                root["text"] = rootnode.name
                root["id"] = rootnode.id
                group_name = ""
                if rootnode.group:
                    group_id = rootnode.group
                    group_name = Group.objects.filter(id=group_id)[0].name

                root["data"] = {"time": rootnode.time, "approval": rootnode.approval, "skip": rootnode.skip,
                                "allgroups": group_string, "group": rootnode.group, "group_name": group_name,
                                "scripts": script_string, "errors": errors, "title": title,
                                "verifyitems": verify_items_string}
                root["children"] = get_step_tree(rootnode, selectid)
                root["state"] = {"opened": True}
                treedata.append(root)
        process = {}
        process["text"] = process_name
        process["data"] = {"allgroups": group_string, "verify": "first_node"}
        process["children"] = treedata
        process["state"] = {"opened": True}
        return JsonResponse({"treedata": process})
    else:
        return HttpResponseRedirect("/login")


def processconfig(request, funid):
    if request.user.is_authenticated():
        process_id = request.GET.get("process_id", "")
        if process_id:
            process_id = int(process_id)

        processes = Process.objects.exclude(state="9").order_by("sort").filter(type="falconstor")
        processlist = []
        for process in processes:
            processlist.append({"id": process.id, "code": process.code, "name": process.name})
        return render(request, 'processconfig.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "processlist": processlist, "process_id": process_id})


def del_step(request):
    if request.user.is_authenticated():
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


def move_step(request):
    if request.user.is_authenticated():
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


def get_all_groups(request):
    if request.user.is_authenticated():
        all_group_list = []
        all_groups = Group.objects.exclude(state="9")
        for num, group in enumerate(all_groups):
            # if num == 0:
            #     group_info_dict = {
            #         "group_id": None,
            #         "group_name": "-----------------",
            #     }
            # else:
            group_info_dict = {
                "group_id": group.id,
                "group_name": group.name,
            }
            all_group_list.append(group_info_dict)
        return JsonResponse({"data": all_group_list})


def process_design(request, funid):
    if request.user.is_authenticated():
        return render(request, "processdesign.html",
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})


def process_data(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        all_process = Process.objects.exclude(state="9").filter(type="falconstor")
        if (len(all_process) > 0):
            for process in all_process:
                result.append({
                    "process_id": process.id,
                    "process_code": process.code,
                    "process_name": process.name,
                    "process_remark": process.remark,
                    "process_sign": process.sign,
                    "process_rto": process.rto,
                    "process_rpo": process.rpo,
                    "process_sort": process.sort,
                })
        return JsonResponse({"data": result})


def process_save(request):
    if request.user.is_authenticated() and request.session['isadmin']:
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
                    if sign.strip() == '':
                        result["res"] = '是否签到不能为空。'
                    else:
                        if id == 0:
                            all_process = Process.objects.filter(code=code).exclude(
                                state="9").filter(type="falconstor")
                            if (len(all_process) > 0):
                                result["res"] = '预案编码:' + code + '已存在。'
                            else:
                                processsave = Process()
                                processsave.code = code
                                processsave.name = name
                                processsave.remark = remark
                                processsave.sign = sign
                                processsave.rto = rto if rto else None
                                processsave.rpo = rpo if rpo else None
                                processsave.sort = sort if sort else None
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
                                    processsave.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = processsave.id
                                except:
                                    result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


def process_del(request):
    if request.user.is_authenticated():
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


def falconstorswitch(request, funid, process_id):
    if request.user.is_authenticated():
        all_wrapper_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=None)
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
            all_wrapper_scripts = wrapper_step.script_set.exclude(state="9")
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
            all_inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=pnode_id)
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
                all_inner_scripts = inner_step.script_set.exclude(state="9")
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
        return render(request, 'falconstorswitch.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "wrapper_step_list": wrapper_step_list, "process_id": process_id})
    else:
        return HttpResponseRedirect("/login")


def falconstorswitchdata(request):
    if request.user.is_authenticated():
        result = []
        all_processrun_objs = ProcessRun.objects.exclude(state="9").order_by("-starttime")

        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止",
            "": "",
        }
        for processrun_obj in all_processrun_objs:
            if processrun_obj.process.type == "falconstor":
                create_user = processrun_obj.creatuser
                create_user_fullname = ""
                if create_user:
                    try:
                        create_user_fullname = UserInfo.objects.filter(user__username=create_user)[0].fullname
                    except:
                        create_user_fullname = ""
                result.append({
                    "starttime": processrun_obj.starttime.strftime(
                        '%Y-%m-%d %H:%M:%S') if processrun_obj.starttime else "",
                    "endtime": processrun_obj.endtime.strftime('%Y-%m-%d %H:%M:%S') if processrun_obj.endtime else "",
                    "createuser": create_user_fullname,
                    "state": state_dict["{0}".format(processrun_obj.state)] if processrun_obj.state else "",
                    "process_id": processrun_obj.process_id if processrun_obj.process_id else "",
                    "processrun_id": processrun_obj.id if processrun_obj.id else "",
                    "run_reason": processrun_obj.run_reason[:20] if processrun_obj.run_reason else "",
                    "process_name": processrun_obj.process.name if processrun_obj.process.name else "",
                    "process_url": processrun_obj.process.url if processrun_obj.process.url else ""
                })
        return JsonResponse({"data": result})


def falconstorrun(request):
    if request.user.is_authenticated():
        result = {}
        processid = request.POST.get('processid', '')
        run_person = request.POST.get('run_person', '')
        run_time = request.POST.get('run_time', '')
        run_reason = request.POST.get('run_reason', '')
        try:
            processid = int(processid)
        except:
            raise Http404()
        process = Process.objects.filter(id=processid).exclude(state="9").filter(type="falconstor")
        if (len(process) <= 0):
            result["res"] = '流程启动失败，该流程不存在。'
        else:
            curprocessrun = ProcessRun.objects.filter(process=process[0], state="RUN")
            if (len(curprocessrun) > 0):
                result["res"] = '流程启动失败，该流程正在进行中，请勿重复启动。'
            else:
                myprocessrun = ProcessRun()
                myprocessrun.process = process[0]
                myprocessrun.starttime = datetime.datetime.now()
                myprocessrun.creatuser = request.user.username
                myprocessrun.run_reason = run_reason
                myprocessrun.state = "RUN"
                myprocessrun.DataSet_id = 89
                myprocessrun.save()
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
                        # print(myscript)
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
                        for group in allgroup:
                            print(group)
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
                            myprocesstask.content = "流程已启动。"
                            myprocesstask.save()

                            # exec_process.delay(myprocessrun.id)
                            result["res"] = "新增成功。"
                            result["data"] = process[0].url + "/" + str(myprocessrun.id)
        return HttpResponse(json.dumps(result))


def falconstor(request, offset, funid):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        return render(request, 'falconstor.html',
                      {'username': request.user.userinfo.fullname, "process": id,
                       "pagefuns": getpagefuns(funid, request)})
    else:
        return HttpResponseRedirect("/index")


def getchildrensteps(processrun, curstep):
    childresult = []
    steplist = Step.objects.exclude(state="9").filter(pnode=curstep)
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
                start_time = steprunlist[0].starttime.replace(tzinfo=None)
                current_time = datetime.datetime.now()
                current_delta_time = (current_time - start_time).total_seconds()
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
        scriptlist = Script.objects.exclude(state="9").filter(step=step)
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
            scripts.append({"id": script.id, "code": script.code, "name": script.name, "runscriptid": runscriptid,
                            "scriptstarttime": scriptstarttime,
                            "scriptendtime": scriptendtime, "scriptoperator": scriptoperator,
                            "scriptrunresult": scriptrunresult, "scriptexplain": scriptexplain,
                            "scriptrunlog": scriptrunlog, "scriptstate": scriptstate})
        childresult.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                            "skip": step.skip, "group": group, "time": step.time, "runid": runid,
                            "starttime": starttime,
                            "endtime": endtime, "operator": operator, "parameter": parameter, "runresult": runresult,
                            "explain": explain, "state": state, "scripts": scripts, "verifyitems": verifyitems,
                            "note": note, "rto": rto,
                            "children": getchildrensteps(processrun, step)})
    return childresult


def getrunsetps(request):
    if request.user.is_authenticated():
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
            try:
                processrun = int(processrun)
            except:
                raise Http404()
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

                processresult["step"] = result
                processresult["process_name"] = process_name
                processresult["process_state"] = process_state
                processresult["process_starttime"] = process_starttime
                processresult["process_endtime"] = process_endtime
                processresult["process_note"] = process_note
                processresult["process_rto"] = process_rto

                steplist = Step.objects.exclude(state="9").filter(process=processruns[0].process, pnode=None)
                for step in steplist:
                    runid = 0
                    starttime = ""
                    endtime = ""
                    operator = ""
                    parameter = ""
                    runresult = ""
                    explain = ""
                    state = ""
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
                            start_time = steprunlist[0].starttime.replace(tzinfo=None)
                            current_time = datetime.datetime.now()
                            current_delta_time = (current_time - start_time).total_seconds()
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
                    scriptlist = Script.objects.exclude(state="9").filter(step=step)
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
                                   "starttime": starttime,
                                   "endtime": endtime, "operator": operator, "parameter": parameter,
                                   "runresult": runresult,
                                   "explain": explain, "state": state, "scripts": scripts, "verifyitems": verifyitems,
                                   "note": note, "rto": rto,
                                   "children": getchildrensteps(processruns[0], step)})

            return HttpResponse(json.dumps(processresult))


def falconstorcontinue(request):
    if request.user.is_authenticated():
        result = {}
        process = request.POST.get('process', '')
        try:
            process = int(process)
        except:
            raise Http404()
        # exec_process.delay(process)
        result["res"] = "执行成功。"
        return HttpResponse(json.dumps(result))


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
            prosstask = ProcessTask.objects.get(id=id)
            prosstask.operator = request.user.username
            prosstask.explain = sign_info
            prosstask.endtime = datetime.datetime.now()
            prosstask.state = "1"
            prosstask.save()

            myprocessrun = prosstask.processrun
            prosssigns = ProcessTask.objects.filter(processrun=myprocessrun, state="0")
            if len(prosssigns) <= 0:
                myprocess = myprocessrun.process
                myprocesstask = ProcessTask()
                myprocesstask.processrun = myprocessrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "START"
                myprocesstask.state = "1"
                myprocesstask.content = "流程已启动。"
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = request.user.username
                myprocesstask.save()

                # exec_process.delay(myprocessrun.id)
                result["res"] = "签字成功,同时启动流程。"
                result["data"] = myprocess.url + "/" + str(myprocessrun.id)
            else:
                result["res"] = "签字成功。"
        except:
            result["res"] = "流程启动失败，请于管理员联系。"
        return JsonResponse(result)


def get_current_scriptinfo(request):
    if request.user.is_authenticated():
        current_step_id = request.POST.get('steprunid', '')
        selected_script_id = request.POST.get('scriptid', '')
        try:
            scriptrun_obj = ScriptRun.objects.filter(id=selected_script_id)[0]
        except:
            scriptrun_obj = None
        script_id = scriptrun_obj.script_id
        try:
            script_obj = Script.objects.filter(id=script_id)[0]
        except:
            script_obj = None
        if script_obj:
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
            starttime = ""
            endtime = ""
            try:
                starttime = scriptrun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            try:
                endtime = scriptrun_obj.endtime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            script_info = {
                "processrunstate": scriptrun_obj.steprun.processrun.state,
                "code": script_obj.code,
                "ip": script_obj.ip,
                "port": script_obj.port,
                "filename": script_obj.filename,
                "scriptpath": script_obj.scriptpath,
                "state": state_dict["{0}".format(scriptrun_obj.state)],
                "starttime": starttime,
                "endtime": endtime,
                "operator": scriptrun_obj.operator,
                "explain": scriptrun_obj.explain,
                "show_button": show_button,
                "step_id_from_script": step_id_from_script
            }

            return JsonResponse({"data": script_info})


def ignore_current_script(request):
    if request.user.is_authenticated():
        selected_script_id = request.POST.get('scriptid', '')
        scriptruns = ScriptRun.objects.filter(id=selected_script_id)[0]
        scriptruns.state = "IGNORE"
        scriptruns.save()
        return JsonResponse({"data": "成功忽略当前脚本"})


def stop_current_process(request):
    if request.user.is_authenticated():
        process_run_id = request.POST.get('process_run_id', '')
        process_note = request.POST.get('process_note', '')

        if process_run_id:
            process_run_id = int(process_run_id)
        else:
            return Http404()

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
            #         else:
            #             return JsonResponse({"data": "流程已结束，终止流程失败"})
            # else:
            #     return JsonResponse({"data": "流程已结束，终止流程失败"})

            current_process_run.state = "STOP"
            current_process_run.endtime = datetime.datetime.now()
            current_process_run.note = process_note
            current_process_run.save()

            all_tasks_ever = current_process_run.processtask_set.all()
            for task in all_tasks_ever:
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
            return JsonResponse({"data": "流程已经被终止"})
        else:
            return JsonResponse({"data": "终止流程异常，请联系客服"})




import pdfkit
from django.template.response import TemplateResponse


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
        return Http404()

    # 2.报表封页文字
    title_xml = "飞康自动化恢复流程"
    abstract_xml = "切换报告"

    # 3.章节名称
    ele_xml01 = "一、切换概述"
    ele_xml02 = "二、步骤详情"

    # 4.构造第一章数据: first_el_dict
    # 切换概述节点下内容,有序字典中存放
    first_el_dict = dict()

    start_time = process_run_obj.starttime
    end_time = process_run_obj.endtime
    create_user = process_run_obj.creatuser
    users = User.objects.filter(username=create_user)
    if users:
        create_user = users[0].userinfo.fullname
    else:
        return Http404()
    run_reason = process_run_obj.run_reason

    first_el_dict["start_time"] = r"{0}".format(
        start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "")
    first_el_dict["end_time"] = r"{0}".format(
        end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "")

    if end_time and start_time:
        delta_time = (end_time - start_time)
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        delta_seconds = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
            start_time, '%Y-%m-%d %H:%M:%S')
        delta_second = str(delta_seconds).split(":")[-1]

        delta_time_str = str(delta_time)
        if delta_time.total_seconds() > 0:
            if "," in delta_time_str:
                delta_time_example = str(delta_time.total_seconds() // 60 // 60).split(".")[0]
                delta_time_list = delta_time_str.split(",")[-1].split(":")
                delta_time = "{0}时{1}分{2}秒".format(delta_time_example, delta_time_list[1],
                                                   delta_second if delta_second else "")
            else:
                delta_time_list = delta_time_str.split(":")
                delta_time = "{0}时{1}分{2}秒".format(delta_time_list[0], delta_time_list[1],
                                                   delta_second if delta_second else "")
        elif delta_time.total_seconds() == 0:
            delta_time = ""
        else:
            return Http404()

        first_el_dict["rto"] = r"{0}".format(delta_time)
    else:
        first_el_dict["rto"] = r"{0}".format("")
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
            second_el_dict["start_time"] = pnode_steprun[0].starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                pnode_steprun[
                    0].starttime else ""
            second_el_dict["end_time"] = pnode_steprun[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if pnode_steprun[
                0].endtime else ""

            if pnode_steprun[0].endtime and pnode_steprun[0].starttime:
                delta_time = (pnode_steprun[0].endtime - pnode_steprun[0].starttime)
                delta_time_str = str(delta_time)

                end_time = pnode_steprun[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                start_time = pnode_steprun[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                delta_seconds = datetime.datetime.strptime(end_time,
                                                           '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                    start_time, '%Y-%m-%d %H:%M:%S')
                delta_second = str(delta_seconds).split(":")[-1]

                if delta_time.total_seconds() > 0:
                    if "," in delta_time_str:
                        delta_time_example = str(delta_time.total_seconds() // 60 // 60).split(".")[0]
                        delta_time_list = delta_time_str.split(",")[-1].split(":")
                        delta_time = "{0}时{1}分{2}秒".format(delta_time_example, delta_time_list[1],
                                                           delta_second if delta_second else "")
                    else:
                        delta_time_list = delta_time_str.split(":")
                        delta_time = "{0}时{1}分{2}秒".format(delta_time_list[0], delta_time_list[1],
                                                           delta_second if delta_second else "")
                elif delta_time.total_seconds() == 0:
                    delta_time = ""
                else:
                    return Http404()

                second_el_dict["rto"] = delta_time
            else:
                second_el_dict["rto"] = ""

        # 步骤负责人
        try:
            users = User.objects.filter(username=pnode_steprun[0].operator)
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

        current_scripts = Script.objects.exclude(state="9").filter(step_id=pstep.id)
        script_list_wrapper = []
        if current_scripts:
            for snum, current_script in enumerate(current_scripts):
                script_el_dict = dict()
                # title
                script_name = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                script_el_dict["script_name"] = script_name
                # content
                steprun_id = pnode_steprun[0].id
                script_id = current_script.id
                current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id, script_id=script_id)
                if current_scriptrun_obj:
                    script_el_dict["start_time"] = current_scriptrun_obj[0].starttime.strftime(
                        "%Y-%m-%d %H:%M:%S") if \
                        current_scriptrun_obj[0].starttime else ""
                    script_el_dict["end_time"] = current_scriptrun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if \
                        current_scriptrun_obj[0].endtime else ""

                    if current_scriptrun_obj[0].endtime and current_scriptrun_obj[0].starttime:
                        delta_time = (current_scriptrun_obj[0].endtime - current_scriptrun_obj[0].starttime)
                        delta_time_str = str(delta_time)

                        end_time = current_scriptrun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                        start_time = current_scriptrun_obj[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                        delta_seconds = datetime.datetime.strptime(end_time,
                                                                   '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                            start_time, '%Y-%m-%d %H:%M:%S')
                        delta_second = str(delta_seconds).split(":")[-1]

                        if delta_time.total_seconds() > 0:
                            if "," in delta_time_str:
                                delta_time_example = str(delta_time.total_seconds() // 60 // 60).split(".")[0]
                                delta_time_list = delta_time_str.split(",")[-1].split(":")
                                delta_time = "{0}时{1}分{2}秒".format(delta_time_example, delta_time_list[1],
                                                                   delta_second if delta_second else "")
                            else:
                                delta_time_list = delta_time_str.split(":")
                                delta_time = "{0}时{1}分{2}秒".format(delta_time_list[0], delta_time_list[1],
                                                                   delta_second if delta_second else "")
                        elif delta_time.total_seconds() == 0:
                            delta_time = ""
                        else:
                            return Http404()

                        script_el_dict["rto"] = delta_time
                    else:
                        script_el_dict["rto"] = ""

                    state = current_scriptrun_obj[0].state
                    if state in state_dict.keys():
                        script_el_dict["state"] = state_dict[state]
                    else:
                        script_el_dict["state"] = ""
                    script_el_dict["explain"] = current_scriptrun_obj[0].explain

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
                    inner_second_el_dict["start_time"] = steprun_obj[0].starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                        steprun_obj[0].starttime else ""
                    inner_second_el_dict["end_time"] = steprun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if \
                        steprun_obj[0].endtime else ""

                    if steprun_obj[0].endtime and steprun_obj[0].starttime:
                        delta_time = (steprun_obj[0].endtime - steprun_obj[0].starttime)
                        delta_time_str = str(delta_time)

                        end_time = steprun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                        start_time = steprun_obj[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                        delta_seconds = datetime.datetime.strptime(end_time,
                                                                   '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                            start_time, '%Y-%m-%d %H:%M:%S')
                        delta_second = str(delta_seconds).split(":")[-1]

                        if delta_time.total_seconds() > 0:
                            if "," in delta_time_str:
                                delta_time_example = str(delta_time.total_seconds() // 60 // 60).split(".")[0]
                                delta_time_list = delta_time_str.split(",")[-1].split(":")
                                delta_time = "{0}时{1}分{2}秒".format(delta_time_example, delta_time_list[1],
                                                                   delta_second if delta_second else "")
                            else:
                                delta_time_list = delta_time_str.split(":")
                                delta_time = "{0}时{1}分{2}秒".format(delta_time_list[0], delta_time_list[1],
                                                                   delta_second if delta_second else "")
                        elif delta_time.total_seconds() == 0:
                            delta_time = ""
                        else:
                            return Http404()

                        inner_second_el_dict["rto"] = delta_time
                    else:
                        inner_second_el_dict["rto"] = ""

                    # ...需要审批时
                    # if step.approval == "1":
                    # 步骤负责人
                    users = User.objects.filter(username=steprun_obj[0].operator)
                    if users:
                        operator = users[0].userinfo.fullname
                        inner_second_el_dict["operator"] = operator
                    else:
                        inner_second_el_dict["operator"] = ""

                    # 当前步骤下脚本
                    current_scripts = Script.objects.exclude(state="9").filter(step_id=step.id)

                    script_list_inner = []
                    if current_scripts:
                        for snum, current_script in enumerate(current_scripts):
                            script_el_dict_inner = dict()
                            # title
                            script_name = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                            script_el_dict_inner["script_name"] = script_name

                            # content
                            steprun_id = steprun_obj[0].id
                            script_id = current_script.id
                            current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id,
                                                                             script_id=script_id)
                            script_el_dict_inner["start_time"] = current_scriptrun_obj[0].starttime.strftime(
                                "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj[0].starttime else ""
                            script_el_dict_inner["end_time"] = current_scriptrun_obj[0].endtime.strftime(
                                "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj[0].endtime else ""

                            if current_scriptrun_obj[0].endtime and current_scriptrun_obj[0].starttime:

                                delta_time = (current_scriptrun_obj[0].endtime - current_scriptrun_obj[
                                    0].starttime)
                                delta_time_str = str(delta_time)

                                end_time = current_scriptrun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S")
                                start_time = current_scriptrun_obj[0].starttime.strftime("%Y-%m-%d %H:%M:%S")
                                delta_seconds = datetime.datetime.strptime(end_time,
                                                                           '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                    start_time, '%Y-%m-%d %H:%M:%S')
                                delta_second = str(delta_seconds).split(":")[-1]

                                if delta_time.total_seconds() > 0:
                                    if "," in delta_time_str:
                                        delta_time_example = \
                                            str(delta_time.total_seconds() // 60 // 60).split(".")[0]
                                        delta_time_list = delta_time_str.split(",")[-1].split(":")
                                        delta_time = "{0}时{1}分{2}秒".format(delta_time_example,
                                                                           delta_time_list[1],
                                                                           delta_second if delta_second else "")
                                    else:
                                        delta_time_list = delta_time_str.split(":")
                                        delta_time = "{0}时{1}分{2}秒".format(delta_time_list[0],
                                                                           delta_time_list[1],
                                                                           delta_second if delta_second else "")
                                elif delta_time.total_seconds() == 0:
                                    delta_time = ""
                                else:
                                    return Http404()

                                script_el_dict_inner["rto"] = delta_time
                            else:
                                script_el_dict_inner["rto"] = ""

                            state = current_scriptrun_obj[0].state
                            if state in state_dict.keys():
                                script_el_dict_inner["state"] = state_dict[state]
                            else:
                                script_el_dict_inner["state"] = ""

                            script_el_dict_inner["explain"] = current_scriptrun_obj[0].explain
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

    # 指定wkhtmltopdf运行程序路径
    current_path = os.getcwd()
    wkhtmltopdf_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "process" + os.sep + "wkhtmltopdf" + os.sep + "bin" + os.sep + "wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

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

    def file_iterator(file_name, chunk_size=512):
        with open(file_name, "rb") as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    the_file_name = "falconstor.pdf"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream; charset=unicode'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


def falconstorsearch(request, funid):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        all_processes = Process.objects.exclude(state="9").filter(type="falconstor")
        processname_list = []
        for process in all_processes:
            processname_list.append(process.name)

        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止"
        }
        return render(request, "falconstorsearch.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "processname_list": processname_list, "state_dict": state_dict,
                       "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def falconstorsearchdata(request):
    """
    :param request: starttime, endtime, runperson, runstate
    :return: starttime,endtime,createuser,state,process_id,processrun_id,runreason
    """
    if request.user.is_authenticated():
        result = []
        processname = request.GET.get('processname', '')
        runperson = request.GET.get('runperson', '')
        runstate = request.GET.get('runstate', '')
        startdate = request.GET.get('startdate', '')
        enddate = request.GET.get('enddate', '')
        start_time = datetime.datetime.strptime(startdate, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
            seconds=1)
        all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
            starttime__range=[start_time, end_time]).order_by("-starttime")

        if runperson:
            if processname != "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    process__name=processname,
                    state=runstate, creatuser=runperson).order_by("-starttime")
            if processname == "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    state=runstate, creatuser=runperson).order_by("-starttime")
            if processname != "" and runstate == "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    process__name=processname, creatuser=runperson).order_by("-starttime")
        else:
            if processname != "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    process__name=processname,
                    state=runstate).order_by("-starttime")
            if processname == "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    state=runstate).order_by("-starttime")
            if processname != "" and runstate == "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(
                    starttime__range=[start_time, end_time],
                    process__name=processname).order_by("-starttime")
        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止",
            "": "",
        }
        for processrun_obj in all_processrun_objs:
            result.append({
                "starttime": processrun_obj.starttime.strftime('%Y-%m-%d %H:%M:%S') if processrun_obj.starttime else "",
                "endtime": processrun_obj.endtime.strftime('%Y-%m-%d %H:%M:%S') if processrun_obj.endtime else "",
                "createuser": processrun_obj.creatuser if processrun_obj.creatuser else "",
                "state": state_dict["{0}".format(processrun_obj.state)] if processrun_obj.state else "",
                "process_id": processrun_obj.process_id if processrun_obj.process_id else "",
                "processrun_id": processrun_obj.id if processrun_obj.id else "",
                "run_reason": processrun_obj.run_reason[:20] if processrun_obj.run_reason else "",
                "process_name": processrun_obj.process.name if processrun_obj.process.name else "",
                "process_url": processrun_obj.process.url if processrun_obj.process.url else ""
            })
        return HttpResponse(json.dumps({"data": result}))


def tasksearch(request, funid):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        all_processes = Process.objects.exclude(state="9").filter(type="falconstor")
        processname_list = []
        for process in all_processes:
            processname_list.append(process.name)

        return render(request, "tasksearch.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "processname_list": processname_list, "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def tasksearchdata(request):
    if request.user.is_authenticated():
        result = []
        task_type = request.GET.get('task_type', '')
        has_finished = request.GET.get('has_finished', '')
        startdate = request.GET.get('startdate', '')
        enddate = request.GET.get('enddate', '')
        print("task_type,has_finished,startdate,enddate", task_type, has_finished, startdate, enddate)
        start_time = datetime.datetime.strptime(startdate, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
            seconds=1)

        all_process_task = ProcessTask.objects.exclude(state="9").filter(
            starttime__range=[start_time, end_time]).order_by("-starttime")

        if task_type != "" and has_finished != "":
            all_process_task = ProcessTask.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                             type=task_type,
                                                                             state=has_finished).order_by("-starttime")
        if task_type == "" and has_finished != "":
            all_process_task = ProcessTask.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                             state=has_finished).order_by("-starttime")
        if task_type != "" and has_finished == "":
            all_process_task = ProcessTask.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                             type=task_type).order_by("-starttime")

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
        for task in all_process_task:
            result.append({
                "task_id": task.id,
                "task_content": task.content,
                "starttime": task.starttime.strftime('%Y-%m-%d %H:%M:%S') if task.starttime else "",
                "endtime": task.endtime.strftime('%Y-%m-%d %H:%M:%S') if task.endtime else "",
                "type": type_dict["{0}".format(task.type)] if task.type in type_dict.keys() else "",
                "processrun_id": task.processrun_id if task.processrun_id else "",
                "process_name": task.processrun.process.name if task.processrun.process.name else "",
                "process_url": task.processrun.process.url if task.processrun.process.url else "",
                "has_finished": has_finished_dict[
                    "{0}".format(task.state)] if task.state in has_finished_dict.keys() else "",
            })
        return JsonResponse({"data": result})


def downloadlist(request, funid):
    if request.user.is_authenticated():
        return render(request, "downloadlist.html",
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def download(request):
    if request.user.is_authenticated():
        try:
            def file_iterator(file_name, chunk_size=512):
                with open(file_name, "rb") as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break

            # the_file_name = "/var/www/TSDRM/download/" + request.GET.get('filename', '').replace('^', ' ')
            the_file_name = "download/" + request.GET.get('filename', '').replace('^', ' ')
            response = StreamingHttpResponse(file_iterator(the_file_name))
            response['Content-Type'] = 'application/octet-stream; charset=unicode'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
            return response
        except:
            return HttpResponseRedirect("/downloadlist")
    else:
        return HttpResponseRedirect("/login")


def invite(request):
    if request.user.is_authenticated():
        process_id = request.GET.get("process_id", "")
        start_date = request.GET.get("start_date", "")
        purpose = request.GET.get("purpose", "")
        end_date = request.GET.get("end_date", "")
        process_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M').strftime("%Y-%m-%d")
        nowtime = datetime.datetime.now()
        invite_time = nowtime.strftime("%Y-%m-%d")

        current_processes = Process.objects.filter(id=process_id).filter(type="falconstor")
        process_name = current_processes[0].name if current_processes else ""
        allgroup = current_processes[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
            "group").distinct()
        all_groups = ""
        if allgroup:
            for num, current_group in enumerate(allgroup):
                if num == len(allgroup) - 1:
                    group = Group.objects.get(id=int(current_group["group"]))
                    all_groups += group.name
                else:
                    group = Group.objects.get(id=int(current_group["group"]))
                    all_groups += group.name + "、"
        all_wrapper_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=None)
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
            all_wrapper_scripts = wrapper_step.script_set.exclude(state="9")
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
            all_inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id, pnode_id=pnode_id)
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
                all_inner_scripts = inner_step.script_set.exclude(state="9")
                for inner_script in all_inner_scripts:
                    inner_script_dict = {
                        "inner_script_name": inner_script.name
                    }
                    inner_script_list.append(inner_script_dict)

                inner_step_dict["inner_script_list"] = inner_script_list

                inner_verify_list = []
                all_inner_verifys = inner_step.verifyitems_set.exclude(state="9")
                for inner_verify in all_inner_verifys:
                    inner_verify_dict = {
                        "inner_verify_name": inner_verify.name
                    }
                    inner_verify_list.append(inner_verify_dict)

                inner_step_dict["inner_verify_list"] = inner_verify_list

                inner_step_list.append(inner_step_dict)

            wrapper_step_dict["inner_step_list"] = inner_step_list

            wrapper_step_list.append(wrapper_step_dict)
        # return render(request, 'notice.html',
        #                      {"wrapper_step_list": wrapper_step_list, "person_invited": person_invited,
        #                       "invite_reason": invite_reason, "invite_time": invite_time})
        t = TemplateResponse(request, 'notice.html',
                             {"wrapper_step_list": wrapper_step_list, "process_date": process_date,
                              "purpose": purpose, "invite_time": invite_time, "start_date": start_date,
                              "end_date": end_date,
                              "process_name": process_name, "all_groups": all_groups})
        t.render()

        # 指定wkhtmltopdf运行程序路径
        current_path = os.getcwd()
        wkhtmltopdf_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "process" + os.sep + "wkhtmltopdf" + os.sep + "bin" + os.sep + "wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
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

        pdfkit.from_string(t.content.decode(encoding="utf-8"), r"invitation.pdf", configuration=config, options=options,
                           css=css)

        def file_iterator(file_name, chunk_size=512):
            with open(file_name, "rb") as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break

        the_file_name = "invitation.pdf"
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
        return response


def get_all_users(request):
    if request.user.is_authenticated():
        all_users = UserInfo.objects.exclude(user=None)
        user_string = ""
        for user in all_users:
            user_string += user.fullname + "&"
        return JsonResponse({"data": user_string})
