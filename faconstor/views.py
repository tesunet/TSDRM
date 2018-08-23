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
from faconstor.CVApi import *
from faconstor.tasks import *
from django.db.models import Count
from django.db.models import Sum, Max
from django.db import connection
from faconstor.vmApi import *
import xlrd, xlwt
import pythoncom
import pymssql
from lxml import etree
from django.forms.models import model_to_dict

pythoncom.CoInitialize()
import wmi

info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
        "lastlogin": 0}


def test(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        return render(request, 'test.html',
                      {'username': request.user.userinfo.fullname, "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def index(request):
    # pythoncom.CoInitialize()
    # conn = wmi.WMI(computer="192.168.100.151", user="administrator", password="tesunet@2017")
    # filename = r"E:\hahah.bat"  # 此文件在远程服务器上
    # cmd_callbat = r"cmd /c call %s" % filename
    # conn.Win32_Process.Create(CommandLine=cmd_callbat)  # 执行bat文件
    # print("执行成功!")
    if request.user.is_authenticated():
        cvvendor = Vendor.objects.filter(name='CommVault')
        if (len(cvvendor) > 0):
            doc = parseString(cvvendor[0].content)
            try:
                webaddr = (doc.getElementsByTagName("webaddr"))[0].childNodes[0].data
            except:
                pass
            try:
                port = (doc.getElementsByTagName("port"))[0].childNodes[0].data
            except:
                pass
            try:
                username = (doc.getElementsByTagName("username"))[0].childNodes[0].data
            except:
                pass
            try:
                passwd = (doc.getElementsByTagName("passwd"))[0].childNodes[0].data
            except:
                pass
            global info
            info = {"webaddr": webaddr, "port": port, "username": username, "passwd": passwd, "token": "",
                    "lastlogin": 0}

        alltask = []
        mygroup = []
        userinfo = request.user.userinfo
        guoups = userinfo.group.all()
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
                myurl = task.processrun.process.url + "/" + str(task.processrun_id)
                process_type = task.type
                if process_type == "SIGN":
                    pop = True
                else:
                    pop = False
                time = ""
                time = task.starttime
                time = time.replace(tzinfo=None)
                timenow = datetime.datetime.now()
                days = int((timenow - time).days)
                hours = int((timenow - time).seconds / 3600)
                task_id = task.id

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

                alltask.append({"content": task.content, "myurl": myurl, "time": time, "pop": pop, "task_id": task_id,
                                "process_name": process_name, "send_time": send_time,
                                "process_run_reason": process_run_reason, "group_name": guoups[0].name})
        # cvToken = CV_RestApi_Token()
        # cvToken.login(info)
        # cvAPI = CV_API(cvToken)
        # clientInfo = cvAPI.getClientInfo(3)
        # backupInfo = cvAPI.getSubclientInfo("22")
        # print uuid.uuid1()
        # print clientInfo
        # print cvAPI.getClientList()
        # 进度
        if not is_connection_usable():
            connection.close()
        try:
            conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX',
                                   database='CommServ')
            cur = conn.cursor()
            cur.execute(
                """SELECT *  FROM [commserv].[dbo].[RunningBackups]""")
            backup_task_list = cur.fetchall()

            cur.execute(
                """SELECT *  FROM [commserv].[dbo].[RunningRestores]""")
            restore_task_list = cur.fetchall()

            # 告警
            nowtime = datetime.datetime.now()
            dttime = datetime.datetime.strptime(
                ((nowtime - datetime.timedelta(days=28 + nowtime.weekday())).strftime("%Y-%m-%d")), '%Y-%m-%d')
            jobid_list = []
            display_error_joblist = []
            joblist = Joblist.objects.values_list("jobid")
            for job in joblist:
                jobid_list.append(job[0])
            cur.execute(
                """select * from [commserv].[dbo].[CommCellBackupInfo] where startdate>='{0}' and jobstatus!='Success'""".format(
                    dttime))
            error_joblist = cur.fetchall()
            for error_job in error_joblist:
                if error_job[0] not in jobid_list:
                    display_error_joblist.append({
                        "jobid": error_job[0],
                        "appid": error_job[1],
                        "jobinitfrom": error_job[2],
                        "clientname": error_job[3],
                        "idataagent": error_job[4],
                        "instance": error_job[5],
                        "backupset": error_job[6],
                        "subclient": error_job[7],
                        "data_sp": error_job[8],
                        "backuplevelInt": error_job[9],
                        "backuplevel": error_job[10],
                        "incrlevel": error_job[11],
                        "jobstatusInt": error_job[12],
                        "jobstatus": error_job[13],
                        "jobfailedreason": error_job[14],
                        "transferTime": error_job[15],
                        "startdateunixsec": error_job[16],
                        "enddateunixsec": error_job[17],
                        "startdate": error_job[18],
                        "enddate": error_job[19],
                        "durationunixsec": error_job[20],
                        "duration": error_job[21],
                        "numstreams": error_job[22],
                        "numbytesuncomp": error_job[23],
                        "numbytescomp": error_job[24],
                        "numobjects": error_job[25],
                        "isAged": error_job[26],
                        "isAgedStr": error_job[27],
                        "xmlJobOptions": error_job[28],
                        "retentionDays": error_job[29],
                        "systemStateBackup": error_job[30],
                        "inPrimaryCopy": error_job[31],
                        "failedobjects": error_job[32],
                        "totalBackupSize": error_job[33],
                        "encrypted": error_job[34],
                    })
            cur.close()
            conn.close()
        except:
            backup_task_list = []
            restore_task_list = []
            display_error_joblist = []
        return render(request, "index.html",
                      {'username': request.user.userinfo.fullname, "alltask": alltask, "homepage": True,
                       "backup_task_list": backup_task_list, "restore_task_list": restore_task_list,
                       "display_error_joblist": display_error_joblist})
    else:
        return HttpResponseRedirect("/login")


def is_connection_usable():
    try:
        connection.connection.ping()
    except:
        return False
    else:
        return True


def get_dashboard_amchart_1(request):
    if request.user.is_authenticated():
        result = []
        times1 = []
        times2 = []
        type = "1"
        try:
            type = request.GET.get('type', '')
        except:
            pass
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        hostlist = []
        if (len(allhost) > 0):
            for host in allhost:
                hostlist.append(host.clientName)
        nowtime = datetime.datetime.now()
        dttime = datetime.datetime.strptime(((nowtime - datetime.timedelta(days=6)).strftime("%Y-%m-%d")), '%Y-%m-%d')
        # select = {'day': connection.ops.date_trunc_sql('day', 'startdate')}
        if type == "2":
            dttime = datetime.datetime.strptime(
                ((nowtime - datetime.timedelta(days=28 + nowtime.weekday())).strftime("%Y-%m-%d")), '%Y-%m-%d')
        if type == "3":
            q, r = divmod(nowtime.month - 1 + 7, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
        if type == "4":
            q, r = divmod(nowtime.month - 1 + 1, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
        fail_status = ["Failed", "Killed", "Failed to Start"]
        if not is_connection_usable():
            connection.close()
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()
        cur.execute(
            """select cast(startdate as date),count(jobid) from [commserv].[dbo].[CommCellBackupInfo] where startdate>='{0}' and clientname in {1} group by cast(startdate as date)""".format(
                dttime, tuple(hostlist)))
        joblist1 = cur.fetchall()
        cur.execute(
            """select cast(startdate as date),count(jobid) from [commserv].[dbo].[CommCellBackupInfo] where startdate>='{0}' and clientname in {1} and jobstatus in {2} group by cast(startdate as date)""".format(
                dttime, tuple(hostlist), tuple(fail_status)))
        joblist2 = cur.fetchall()
        cur.close()
        conn.close()
        # joblist1 = Joblist.objects.filter(startdate__gte=dttime, clientname__in=hostlist).extra(select=select).values("day").annotate(num_day=Count('id')).order_by("day")
        # print("joblist1", joblist1)
        # joblist2 = Joblist.objects.filter(startdate__gte=dttime, clientname__in=hostlist).filter(jobstatus__in=["Failed", "Killed", "Failed to Start"]).extra(select=select).values(
        #     "day").annotate(num_day=Count('id'))
        for job in joblist1:
            times = 0
            try:
                times = int(job[1])
            except:
                pass
            datarow = {"date": job[0], "times": times}
            if type == "3" or type == "4":
                datarow = {"date": job[0], "times": times}
            times1.append(datarow)
        # joblist2 = joblist.filter(jobstatus__in=["Failed", "Killed", "Failed to Start"]).extra(select=select).values(
        #     "day").annotate(num_day=Count('id'))
        for job in joblist2:
            times = 0
            try:
                times = int(job[1])
            except:
                pass
            datarow = {"date": job[0], "times": times}
            if type == "3" or type == "4":
                datarow = {"date": job[0], "times": times}
            times2.append(datarow)
        if type == "1":
            for i in range((nowtime - dttime).days + 1):
                day = dttime + datetime.timedelta(days=i)
                count1 = 0
                count2 = 0
                for time1 in times1:
                    if time1["date"] == day.strftime("%Y-%m-%d"):
                        count1 = time1["times"]
                        break
                for time2 in times2:
                    if time2["date"] == day.strftime("%Y-%m-%d"):
                        count2 = time2["times"]
                        break
                result.append(
                    {"date": day.strftime("%m-%d"), "times1": count1, "times2": count2, "times3": count1 - count2})
        if type == "2":
            count1 = 0
            count2 = 0
            strdt = dttime.strftime("%m-%d")
            for i in range((nowtime - dttime).days + 1):
                day = dttime + datetime.timedelta(days=i)
                for time1 in times1:
                    if time1["date"] == day.strftime("%Y-%m-%d"):
                        count1 += time1["times"]
                        break
                for time2 in times2:
                    if time2["date"] == day.strftime("%Y-%m-%d"):
                        count2 += time2["times"]
                        break
                if day.weekday() == 6 or i == (nowtime - dttime).days:
                    strdt = strdt + "/" + day.strftime("%m-%d")
                    result.append(
                        {"date": strdt, "times1": count1, "times2": count2, "times3": count1 - count2})
                    count1 = 0
                    count2 = 0
                    strdt = (day + datetime.timedelta(days=1)).strftime("%m-%d")
        if type == "3" or type == "4":
            count1 = 0
            count2 = 0
            for i in range((nowtime - dttime).days + 1):
                day = dttime + datetime.timedelta(days=i)
                for time1 in times1:
                    if time1["date"] == day.strftime("%Y-%m-%d"):
                        count1 += time1["times"]
                        break
                for time2 in times2:
                    if time2["date"] == day.strftime("%Y-%m-%d"):
                        count2 += time2["times"]
                        break
                if (day + datetime.timedelta(days=1)).day == 1 or i == (nowtime - dttime).days:
                    result.append(
                        {"date": day.strftime("%y-%m"), "times1": count1, "times2": count2, "times3": count1 - count2})
                    count1 = 0
                    count2 = 0
        return HttpResponse(json.dumps(result))


def get_dashboard_amchart_2(request):
    if request.user.is_authenticated():
        result = []
        times1 = []
        times2 = []
        type = "1"
        try:
            type = request.GET.get('type', '')
        except:
            pass
        hostlist = []
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                hostlist.append(host.clientName)
        nowtime = datetime.datetime.now()
        dttime = datetime.datetime.strptime(((nowtime - datetime.timedelta(days=6)).strftime("%Y-%m-%d")), '%Y-%m-%d')
        select = {'day': connection.ops.date_trunc_sql('day', 'startdate')}
        if type == "2":
            dttime = datetime.datetime.strptime(
                ((nowtime - datetime.timedelta(days=28 + nowtime.weekday())).strftime("%Y-%m-%d")), '%Y-%m-%d')
        if type == "3":
            q, r = divmod(nowtime.month - 1 + 7, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
        if type == "4":
            q, r = divmod(nowtime.month - 1 + 1, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)

        fail_status = ["Failed", "Killed", "Failed to Start"]
        if not is_connection_usable():
            connection.close()
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()

        cur.execute(
            """select clientname,count(jobid),max(startdate) from [commserv].[dbo].[CommCellBackupInfo] group by clientname""")
        joblist1 = cur.fetchall()
        # cur.execute("""select startdate,count(jobid) from [commserv].[dbo].[CommCellBackupInfo] where startdate>='{0}' and clientname in {1} and jobstatus in {2} group by startdate""".format(dttime, tuple(hostlist), tuple(fail_status)))
        # joblist2 = cur.fetchall()
        cur.execute(
            """select clientname,count(jobid) from [commserv].[dbo].[CommCellBackupInfo] where jobstatus in {0} group by clientname""".format(
                tuple(fail_status)))
        joblist2 = cur.fetchall()

        cur.close()
        conn.close()
        # joblist = Joblist.objects.filter(startdate__gte=dttime, clientname__in=hostlist)
        # joblist1 = joblist.values("clientname").annotate(num_clientname=Count('id'))
        for job in joblist1:
            times = 0
            try:
                times = int(job[1])
            except:
                pass
            lastjob = job[2]
            # lastjob = Joblist.objects.filter(clientname=job["clientname"]).latest("startdate")
            times1.append({"clientname": job[0], "times": times,
                           "lasttime": lastjob.strftime("%Y-%m-%d %X")})
        # joblist2 = joblist.filter(jobstatus__in=["Failed", "Killed", "Failed to Start"]).values("clientname").annotate(
        #     num_clientname=Count('id'))
        for job in joblist2:
            times = 0
            try:
                times = int(job[0])
            except:
                pass
            times2.append({"clientname": job[0], "times": times})
        for time1 in times1:
            count1 = time1["times"]
            count2 = 0
            for time2 in times2:
                if time1["clientname"] == time2["clientname"]:
                    count2 = time2["times"]
                    break
            result.append(
                {"clientname": time1["clientname"], "times1": count1, "times2": count2, "times3": count1 - count2,
                 "lasttime": time1["lasttime"]})
        return HttpResponse(json.dumps(result))


def get_dashboard_amchart_3(request):
    if request.user.is_authenticated():
        if not is_connection_usable():
            connection.close()
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()
        result = []
        ll = []
        rl = []
        type = "1"
        try:
            type = request.GET.get('type', '')
        except:
            pass
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        hostlist = []
        if (len(allhost) > 0):
            for host in allhost:
                hostlist.append(host.clientName)
        nowtime = datetime.datetime.now()

        if type == "1":
            dttime = datetime.datetime.strptime(((nowtime - datetime.timedelta(days=6)).strftime("%Y-%m-%d")),
                                                '%Y-%m-%d')
            for i in range(7):
                ll = 0
                day = dttime + datetime.timedelta(days=i)
                s = datetime.datetime(day.year, day.month, day.day).strftime("%Y-%m-%d %H:%M:%S")
                e = (datetime.datetime(day.year, day.month, day.day) + datetime.timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """select sum(numbytesuncomp) from [commserv].[dbo].[CommCellBackupInfo] where clientname in {2} and startdate between '{0}' and '{1}' group by numbytesuncomp""".format(
                        s, e, tuple(hostlist)))
                curjoblist = cur.fetchall()
                # curjoblist = Joblist.objects.filter(startdate__range=(s, e), clientname__in=hostlist).extra(
                #     select={'llsum': 'sum(numbytesuncomp)'}).values('llsum')
                # if curjoblist[0]["llsum"] is not] None:
                #     ll = curjoblist[0]["llsum"]
                if curjoblist:
                    if curjoblist[0][0] is not None:
                        ll = curjoblist[0][0]
                        # print("ll", ll)  # 0???

                rlsum = 0
                for clientname in hostlist:
                    cur.execute(
                        """select startdate, jobid from [commserv].[dbo].[CommCellBackupInfo] where backuplevel='Full' and clientname='{0}' and startdate<='{1}' order by startdate desc""".format(
                            clientname, e))
                    rlfulljoblist = cur.fetchall()
                    # rlfulljoblist = Joblist.objects.filter(startdate__lte=e, backuplevel='Full',
                    #                                        clientname=clientname).order_by("-startdate")
                    rl = 0
                    if len(rlfulljoblist) > 0:
                        job_id = rlfulljoblist[0][1]
                        cur.execute(
                            """SELECT SUM(sizeOnMedia) FROM [commserv].[dbo].[JMJobDataStats] where jobid={0}""".format(
                                job_id))
                        rl = cur.fetchall()[0][0]
                        # rl = rlfulljoblist[0].diskcapacity
                        s = rlfulljoblist[0][0].strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        rlsum = rlsum + rl
                    except:
                        # print("rl为None!")
                        pass
                    cur.execute(
                        """select sum(numbytesuncomp) from [commserv].[dbo].[CommCellBackupInfo] where backuplevel='Incremental' and clientname in {2} and startdate between '{0}' and '{1}' group by numbytesuncomp""".format(
                            s, e, tuple(hostlist)))
                    rlincjoblist = cur.fetchall()

                    # rlincjoblist = Joblist.objects.filter(startdate__range=(s, e), backuplevel='Incremental',
                    #                                       clientname=clientname)
                    # rlincjoblist = rlincjoblist.extra(select={'rlsum': 'sum(numbytesuncomp)'}).values('rlsum')
                    if rlincjoblist:
                        if rlincjoblist[0][0] is not None:
                            rl = rlincjoblist[0][0]
                        rlsum = rlsum + rl
                result.append(
                    {"date": day.strftime("%m-%d"), "ll": int(ll / 1024 / 1024), "rl": int(rlsum / 1024 / 1024)})
        if type == "2":
            dttime = datetime.datetime.strptime(
                ((nowtime - datetime.timedelta(days=28 + nowtime.weekday())).strftime("%Y-%m-%d")), '%Y-%m-%d')
            for i in range(5):
                ll = 0
                day = dttime + datetime.timedelta(days=i * 7)
                s = datetime.datetime(day.year, day.month, day.day)
                e = datetime.datetime(day.year, day.month, day.day) + datetime.timedelta(days=7)
                s1 = s.strftime("%Y-%m-%d %H:%M:%S")
                e1 = e.strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(
                    """select sum(numbytesuncomp) from [commserv].[dbo].[CommCellBackupInfo] where clientname in {2} and startdate between '{0}' and '{1}' group by numbytesuncomp""".format(
                        s1, e1, tuple(hostlist)))
                curjoblist = cur.fetchall()
                if curjoblist:
                    if curjoblist[0][0] is not None:
                        ll = curjoblist[0][0]

                # curjoblist = Joblist.objects.filter(startdate__range=(s, e), clientname__in=hostlist).extra(
                #     select={'llsum': 'sum(numbytesuncomp)'}).values('llsum')
                # if curjoblist[0]["llsum"] is not None:
                #     ll = curjoblist[0]["llsum"]

                rlsum = 0

                result.append({"date": s.strftime("%m-%d") + "/" + e.strftime("%m-%d"), "ll": int(ll / 1024 / 1024),
                               "rl": int(rlsum / 1024 / 1024)})

        if type == "3":
            q, r = divmod(nowtime.month - 1 + 7, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
            for i in range(6):
                ll = 0
                q, r = divmod(dttime.month - 1 + i, 12)
                day = datetime.datetime(dttime.year + q, r + 1, 1)
                s = datetime.datetime(day.year, day.month, day.day)
                q, r = divmod(s.month - 1 + 1, 12)
                e = datetime.datetime(s.year + q, r + 1, 1)
                s1 = datetime.datetime(day.year, day.month, day.day).strftime("%Y-%m-%d %H:%M:%S")
                e1 = datetime.datetime(s.year + q, r + 1, 1).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """select sum(numbytesuncomp) from [commserv].[dbo].[CommCellBackupInfo] where clientname in {2} and startdate between '{0}' and '{1}' group by numbytesuncomp""".format(
                        s1, e1, tuple(hostlist)))
                curjoblist = cur.fetchall()
                if curjoblist:
                    if curjoblist[0][0] is not None:
                        ll = curjoblist[0][0]

                # curjoblist = Joblist.objects.filter(startdate__range=(s, e), clientname__in=hostlist).extra(
                #     select={'llsum': 'sum(numbytesuncomp)'}).values('llsum')
                # if curjoblist[0]["llsum"] is not None:
                #     ll = curjoblist[0]["llsum"]

                rlsum = 0

                result.append(
                    {"date": s.strftime("%y-%m"), "ll": int(ll / 1024 / 1024), "rl": int(rlsum / 1024 / 1024)})
        if type == "4":
            q, r = divmod(nowtime.month - 1 + 1, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
            for i in range(12):
                ll = 0
                q, r = divmod(dttime.month - 1 + i, 12)
                day = datetime.datetime(dttime.year + q, r + 1, 1)
                s = datetime.datetime(day.year, day.month, day.day)
                q, r = divmod(s.month - 1 + 1, 12)
                e = datetime.datetime(s.year + q, r + 1, 1)
                s1 = datetime.datetime(day.year, day.month, day.day).strftime("%Y-%m-%d %H:%M:%S")
                e1 = datetime.datetime(s.year + q, r + 1, 1).strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(
                    """select sum(numbytesuncomp) from [commserv].[dbo].[CommCellBackupInfo] where clientname in {2} and startdate between '{0}' and '{1}' group by numbytesuncomp""".format(
                        s, e, tuple(hostlist)))
                curjoblist = cur.fetchall()
                if curjoblist:
                    if curjoblist[0][0] is not None:
                        ll = curjoblist[0][0]

                # curjoblist = Joblist.objects.filter(startdate__range=(s, e), clientname__in=hostlist).extra(
                #     select={'llsum': 'sum(numbytesuncomp)'}).values('llsum')
                # if curjoblist[0]["llsum"] is not None:
                #     ll = curjoblist[0]["llsum"]

                rlsum = 0

                result.append(
                    {"date": s.strftime("%y-%m"), "ll": int(ll / 1024 / 1024), "rl": int(rlsum / 1024 / 1024)})
        cur.close()
        conn.close()
        return HttpResponse(json.dumps(result))


def get_dashboard_amchart_4(request):
    if request.user.is_authenticated():
        type = "1"
        try:
            type = request.GET.get('type', '')
        except:
            pass
        hostlist = []
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                hostlist.append(host.clientName)
        result = []
        nowtime = datetime.datetime.now()
        dttime = datetime.datetime.strptime(((nowtime - datetime.timedelta(days=6)).strftime("%Y-%m-%d")), '%Y-%m-%d')
        select = {'day': connection.ops.date_trunc_sql('day', 'startdate')}
        if type == "2":
            dttime = datetime.datetime.strptime(
                ((nowtime - datetime.timedelta(days=28 + nowtime.weekday())).strftime("%Y-%m-%d")), '%Y-%m-%d')
        if type == "3":
            q, r = divmod(nowtime.month - 1 + 7, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)
        if type == "4":
            q, r = divmod(nowtime.month - 1 + 1, 12)
            dttime = datetime.datetime(nowtime.year - 1 + q, r + 1, 1)

        fail_status = ["Failed", "Killed", "Failed to Start"]
        if not is_connection_usable():
            connection.close()
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()
        cur.execute(
            """select jobstatus,count(jobid) from [commserv].[dbo].[CommCellBackupInfo] where startdate>='{0}' and clientname in {1} group by jobstatus""".format(
                dttime, tuple(hostlist)))
        joblist = cur.fetchall()

        cur.close()
        conn.close()

        # joblist = Joblist.objects.filter(startdate__gte=dttime, clientname__in=hostlist).values("jobstatus").annotate(
        #     num_jobstatus=Count('jobstatus')).values("jobstatus", "num_jobstatus")
        Completed = 0
        Failed = 0
        errors = 0
        for job in joblist:
            if str(job[0]) == "Success":
                Completed += int(job[1])
            else:
                if str(job[0]) == "Failed":
                    Failed += int(job[1])
                else:
                    if str(job[0]) == "Killed":
                        Failed += int(job[1])
                    else:
                        if str(job[0]) == "Failed to Start":
                            Failed += int(job[1])
                        else:
                            errors = job[1]
        result.append({"country": "成功", "value": Completed})
        result.append({"country": "失败", "value": Failed})
        result.append({"country": "报警", "value": errors})

        return HttpResponse(json.dumps(result))


def not_display_jobs(request):
    if request.user.is_authenticated():
        job_id = request.POST.get("jobid", "")
        result = ''
        if job_id:
            job_obj = Joblist()
            job_obj.jobid = job_id
            job_obj.save()
            result = "0"
        else:
            result = "1"
        return JsonResponse({"result": result})


def downloadlist(request):
    if request.user.is_authenticated():
        return render(request, "downloadlist.html", {'username': request.user.userinfo.fullname, "downloadpage": True})
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


def registUser(request):
    if request.method == 'POST':
        result = ""
        myusername = request.POST.get('username', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')

        alluser = User.objects.filter(username=myusername)
        if (len(alluser) > 0):
            result = u"用户名" + myusername + u'已存在。'
        else:
            alluser = User.objects.filter(email=email)
            if (len(alluser) > 0):
                result = u"邮箱" + email + u'已被注册。'
            else:
                newuser = User()
                newuser.username = myusername
                newuser.set_password("password")
                newuser.email = email
                newuser.save()
                # 用户扩展信息 profile
                profile = UserInfo()  # e*************************
                profile.user_id = newuser.id
                profile.userGUID = uuid.uuid1()
                profile.phone = phone
                profile.type = "1"
                profile.state = "0"
                profile.save()
                result = "success1"
                user = auth.authenticate(username=myusername, password="password")
                if user is not None and user.is_active:
                    auth.login(request, user)
                try:
                    subject = u'注册成功'
                    message = u'用户:' + myusername + u'您好。' \
                              + u"\n您在云灾备系统注册成功，初始密码为password，点击链接进入登录页面:" \
                              + u"http://127.0.0.1:8000/login/"
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
                except:
                    pass
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


def activate(request):
    if request.user.is_authenticated():
        myuser = request.user
        myuserinfo = myuser.userinfo
        if myuserinfo.state == "0":
            company = myuserinfo.company
            fullname = myuserinfo.fullname
            tell = myuserinfo.tell
            if not myuserinfo.company:
                company = ""
            if not myuserinfo.fullname:
                fullname = ""
            if not myuserinfo.tell:
                tell = ""
            return render(request, 'activate.html',
                          {"myusername": myuser.username, "fullname": fullname, "company": company, "tell": tell})
        else:
            return render(request, 'activate.html', {"error": True})
    else:
        return HttpResponseRedirect("/login")


def useractivate(request):
    if request.method == 'POST':
        result = ""
        myusername = request.POST.get('username', '')
        company = request.POST.get('company', '')
        fullname = request.POST.get('fullname', '')
        tell = request.POST.get('tell', '')
        password = request.POST.get('password', '')

        alluser = User.objects.filter(username=myusername)
        if (len(alluser) > 0):
            alluser[0].set_password(password)
            alluser[0].save()

            myuserinfo = alluser[0].userinfo
            myuserinfo.fullname = fullname
            myuserinfo.company = company
            myuserinfo.tell = tell
            myuserinfo.state = "1"
            myuserinfo.save()
            user = auth.authenticate(username=myusername, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                usertype = myuserinfo.type
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = alluser[0].is_superuser
            result = "success"
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


def useredit(request):
    if request.user.is_authenticated():
        myuser = request.user
        myuserinfo = myuser.userinfo
        email = myuser.email
        phone = myuserinfo.phone
        company = myuserinfo.company
        fullname = myuserinfo.fullname
        tell = myuserinfo.tell
        if not myuserinfo.company:
            company = ""
        if not myuserinfo.fullname:
            fullname = ""
        if not myuserinfo.tell:
            tell = ""
        return render(request, 'useredit.html',
                      {'username': request.user.userinfo.fullname, "edituserpage": True, "myusername": myuser.username,
                       "email": email, "phone": phone, "fullname": fullname, "company": company, "tell": tell})
    else:
        return HttpResponseRedirect("/login")


def usersave(request):
    if request.method == 'POST':
        result = ""
        myusername = request.POST.get('username', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        company = request.POST.get('company', '')
        fullname = request.POST.get('fullname', '')
        tell = request.POST.get('tell', '')

        alluser = User.objects.filter(username=myusername)
        if (len(alluser) > 0):
            alluser[0].email = email
            alluser[0].save()
            myuserinfo = alluser[0].userinfo
            myuserinfo.phone = phone
            myuserinfo.fullname = fullname
            myuserinfo.company = company
            myuserinfo.tell = tell
            myuserinfo.save()
            result = "保存成功。"
        else:
            result = "用户异常。"
        return HttpResponse(result)


def childuser(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        return render(request, 'childuser.html', {'username': request.user.userinfo.fullname, "childuserpage": True})
    else:
        return HttpResponseRedirect("/login")


def childuserdata(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        result = []
        myuser = request.user
        myuserinfo = myuser.userinfo
        alluserinfo = UserInfo.objects.filter(pnode=myuserinfo)
        if (len(alluserinfo) > 0):
            for userinfo in alluserinfo:
                user = userinfo.user
                if user.is_active == 1:
                    id = user.id
                    username = user.username
                    email = user.email
                    phone = userinfo.phone
                    company = userinfo.company
                    fullname = userinfo.fullname
                    tell = userinfo.tell
                    selectedhosts = userinfo.client_host.all()
                    selectedhost_list = []
                    for selectedhost in selectedhosts:
                        selectedhost_list.append(selectedhost.clientName)
                    state = "未激活"
                    if userinfo.state == "1":
                        state = "已激活"
                    result.append({"id": id, "username": username, "email": email, "phone": phone, "company": company,
                                   "fullname": fullname, "tell": tell, "state": state,
                                   "selectedhost": selectedhost_list})
        return HttpResponse(json.dumps({"data": result}))


def childusersave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            id = request.POST.get('id', '')
            myusername = request.POST.get('username', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            company = request.POST.get('company', '')
            fullname = request.POST.get('fullname', '')
            tell = request.POST.get('tell', '')

            try:
                id = int(id)
            except:
                raise Http404()

            if id == 0:
                alluser = User.objects.filter(username=myusername)
                if (len(alluser) > 0):
                    result = u"用户名" + myusername + u'已存在。'
                else:
                    alluser = User.objects.filter(email=email)
                    if (len(alluser) > 0):
                        result = u"邮箱" + email + u'已被注册。'
                    else:
                        newuser = User()
                        newuser.username = myusername
                        newuser.set_password("password")
                        newuser.email = email
                        newuser.save()
                        # 用户扩展信息 profile
                        profile = UserInfo()  # e*************************
                        profile.user_id = newuser.id
                        profile.userGUID = uuid.uuid1()
                        profile.pnode = request.user.userinfo
                        profile.phone = phone
                        profile.fullname = fullname
                        profile.company = company
                        profile.tell = tell
                        profile.type = "2"
                        profile.state = "0"
                        profile.save()

                        all_selected_clients = request.POST.getlist('my_multi_select1', '')
                        for client in all_selected_clients:
                            client_obj = ClientHost.objects.filter(clientName=client).filter(
                                Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))[0]
                            newuser.userinfo.client_host.add(client_obj)

                        result = "保存成功。"
                        try:
                            subject = u'注册成功'
                            message = u'用户:' + myusername + u'您好。' \
                                      + "用户" + request.user.userinfo.fullname + u"\n已为您在云灾备系统成功分配账号，初始密码为password，点击链接进入登录页面:" \
                                      + u"http://127.0.0.1:8000/login/"
                            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
                        except:
                            pass
            else:
                alluser = User.objects.filter(username=myusername)
                if (len(alluser) > 0):
                    alluser[0].email = email
                    alluser[0].save()
                    myuserinfo = alluser[0].userinfo

                    all_selected_clients = request.POST.getlist('my_multi_select1', '')
                    myuserinfo.client_host.clear()
                    for client in all_selected_clients:
                        client_obj = ClientHost.objects.filter(clientName=client).filter(
                            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))[0]
                        myuserinfo.client_host.add(client_obj)

                    myuserinfo.phone = phone
                    myuserinfo.fullname = fullname
                    myuserinfo.company = company
                    myuserinfo.tell = tell
                    myuserinfo.save()
                    result = "保存成功。"
                else:
                    result = "用户异常。"
            return HttpResponse(result)


def childuserdel(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            myuser = User.objects.get(id=id)
            myuser.is_active = 0
            myuser.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def getallclients(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            all_host = ClientHost.objects.exclude(status="9").filter(
                Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
            host_list = []
            for host in all_host:
                if (len(all_host) > 0):
                    clientName = host.clientName
                    host_list.append({
                        "clientName": clientName,
                    })
            return JsonResponse({"data": host_list})


def script(request):
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
                      {'username': request.user.userinfo.fullname, "scriptpage": True, "errors": errors})
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


def get_scripts(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        step_id = request.POST.get("step_id", "")
        result = []
        script_objs = Script.objects.exclude(state="9").filter(step_id=step_id)
        for script in script_objs:
            result.append({
                "script_id": script.id,
                "script_code": script.code,
            })
        return HttpResponse(json.dumps({"data": result}))


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


def group(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        allgroup = Group.objects.all().exclude(state="9")
        return render(request, 'group.html',
                      {'username': request.user.userinfo.fullname,
                       "allgroup": allgroup, "grouppage": True})
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
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        allgroup = Group.objects.filter(id=id)
        if (len(allgroup) > 0):
            groupsave = allgroup[0]
            groupsave.state = "9"
            groupsave.save()
            result = "删除成功。"
        else:
            result = '角色不存在。'
        return HttpResponse(result)


def getusers(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        users = UserInfo.objects.all()
        selected_users = UserInfo.objects.filter(group__id=id)
        selected_user_list = []
        for selected_usr in selected_users:
            selected_user_list.append({
                "userid": selected_usr.id,
                "username": selected_usr.fullname
            })
        user_list = []
        for user in users:
            user_list.append({
                "userid": user.id,
                "username": user.fullname
            })

        return JsonResponse({"data": {
            "user_list": user_list,
            "selected_user_list": selected_user_list,
        }
        })


def getselectedusers(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        users = UserInfo.objects.filter(group__id=id)
        users_to_str = ""
        if len(users) > 0:
            for num, user in enumerate(users):
                users_to_str += "&%s" % user.fullname
            return JsonResponse({"data": users_to_str[1:]})


def groupsaveuser(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        selectedusers = request.POST.get('selecteduser', '')
        selectedusers = selectedusers.split('*!-!*')
        try:
            id = int(id)
        except:
            raise Http404()
        groupsave = Group.objects.get(id=id)
        groupsave.userinfo_set.clear()
        if len(selectedusers) > 0:
            for selecteduser in selectedusers:
                try:
                    myuser = UserInfo.objects.get(id=int(selecteduser))
                    myuser.group.add(groupsave)
                except:
                    pass
        return HttpResponse("保存成功。")


def resourcepool(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        return render(request, 'resourcepool.html',
                      {'username': request.user.userinfo.fullname, "resourcepoolpage": True})
    else:
        return HttpResponseRedirect("/login")


def resourcepooldata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9")
        if (len(allresourcepool) > 0):
            for resourcepool in allresourcepool:
                id = resourcepool.id
                name = resourcepool.name
                type = resourcepool.type
                supplier = resourcepool.supplier
                certificate = resourcepool.certificate
                description = resourcepool.description
                doc = parseString(certificate)

                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                        if type == '虚机资源':
                            datacenter = hostnode.getAttribute("datacenter")
                            cluster = hostnode.getAttribute("cluster")
                if type == '虚机资源':
                    result.append(
                        {"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                         "ip": ip, "username": username, "password": password, "cluster": cluster,
                         "datacenter": datacenter})
                else:
                    result.append(
                        {"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                         "ip": ip, "username": username, "password": password})
        return HttpResponse(json.dumps({"data": result}))


def getvendorlist(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            result = []
            type = request.POST.get('type', '')
            vendorlist = Vendor.objects.exclude(status="9").filter(type=type)
            for vendor in vendorlist:
                result.append({"vendorGUID": vendor.vendorGUID, "name": vendor.name})

            return HttpResponse(json.dumps(result))


def resourcepoolsave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            id = request.POST.get('id', '')
            name = request.POST.get('name', '')
            type = request.POST.get('type', '')
            description = request.POST.get('description', '')
            supplier = request.POST.get('supplier', '')
            ip = request.POST.get('ip', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')

            # 获取datacenter cluster
            datacenter = request.POST.get('datacenter', '')
            cluster = request.POST.get('cluster', '')

            try:
                id = int(id)
            except:
                raise Http404()
            if id == 0:  #
                allpool = ResourcePool.objects.filter(name=name)
                if (len(allpool) > 0):
                    result = u"资源池名称" + name + u'已存在。'
                else:
                    newpool = ResourcePool()
                    newpool.name = name
                    newpool.type = type
                    newpool.description = description
                    newpool.supplier = supplier

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'CERT_LIST', None)
                    root = dom.documentElement
                    nameE = dom.createElement('CERT')

                    nameE.setAttribute("ip", ip)  # 增加属性
                    nameE.setAttribute("username", username)  # 增加属性
                    nameE.setAttribute("password", password)  # 增加属性

                    if type == '虚机资源':
                        newpool.datacenter = datacenter
                        newpool.cluster = cluster
                        nameE.setAttribute("datacenter", datacenter)
                        nameE.setAttribute("cluster", cluster)

                    root.appendChild(nameE)
                    newpool.certificate = dom.toxml()

                    newpool.creatdate = datetime.datetime.now()
                    newpool.updatedate = datetime.datetime.now()
                    newpool.state = "0"
                    newpool.save()
                    result = "保存成功。"
            else:
                allpool = ResourcePool.objects.filter(id=id)
                if (len(allpool) > 0):
                    allpool1 = ResourcePool.objects.filter(name=name).exclude(id=id)
                    if (len(allpool1) > 0):
                        result = u"资源池名称" + name + u'已存在。'
                    else:
                        newpool = allpool[0]
                        newpool.name = name
                        newpool.type = type
                        newpool.description = description
                        newpool.supplier = supplier
                        impl = xml.dom.minidom.getDOMImplementation()
                        dom = impl.createDocument(None, 'CERT_LIST', None)
                        root = dom.documentElement
                        nameE = dom.createElement('CERT')
                        nameE.setAttribute("ip", ip)  # 增加属性
                        nameE.setAttribute("username", username)  # 增加属性
                        nameE.setAttribute("password", password)  # 增加属性
                        if type == '虚机资源':
                            newpool.datacenter = datacenter
                            newpool.cluster = cluster
                            nameE.setAttribute("datacenter", datacenter)
                            nameE.setAttribute("cluster", cluster)

                        root.appendChild(nameE)
                        newpool.certificate = dom.toxml()
                        newpool.updatedate = datetime.datetime.now()
                        newpool.save()
                        result = "保存成功。"
                else:
                    result = "数据异常。"
            return HttpResponse(result)


def resourcepooldel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            mypoll = ResourcePool.objects.get(id=id)
            mypoll.name = mypoll.name + u"(已删除)"
            mypoll.state = "9"
            mypoll.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def computerresource(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        return render(request, 'computerresource.html',
                      {'username': request.user.userinfo.fullname, "computerresourcepage": True})
    else:
        return HttpResponseRedirect("/login")


def computerresourcedata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresource = ComputerResource.objects.exclude(state="9")
        if (len(allresource) > 0):
            for resource in allresource:
                id = resource.id
                name = resource.name
                poolid = resource.pool.id
                poolname = resource.pool.name
                certificate = resource.certificate
                specifications = resource.specifications
                description = resource.description
                state = "空闲"
                if resource.state == "1":
                    state = "已使用"
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")

                doc2 = parseString(specifications)
                disks = []
                for node in doc2.getElementsByTagName("SPEC_LIST"):
                    cpu = node.getAttribute("cpu")
                    memory = node.getAttribute("memory")
                    for hostnode in node.getElementsByTagName("DISK"):
                        disk_size = hostnode.getAttribute("size")
                        disk_name = hostnode.getAttribute("name")
                        disk_type = hostnode.getAttribute("type")
                        disks.append({"size": disk_size, "name": disk_name, "type": disk_type})
                result.append(
                    {"id": id, "name": name, "poolid": poolid, "poolname": poolname, "description": description,
                     "state": state, "ip": ip, "username": username, "password": password, "cpu": cpu, "memory": memory,
                     "disks": disks})
        return HttpResponse(json.dumps({"data": result}))


def computerresourcepooldata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9").filter(type="主机资源")
        if (len(allresourcepool) > 0):
            for resourcepool in allresourcepool:
                id = resourcepool.id
                name = resourcepool.name
                type = resourcepool.type
                supplier = resourcepool.supplier
                certificate = resourcepool.certificate
                description = resourcepool.description
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                result.append({"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                               "ip": ip, "username": username, "password": password})
        return HttpResponse(json.dumps({"data": result}))


def computerresourcepooldatafordrill(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9").filter(type="主机资源")
        if (len(allresourcepool) > 0):
            for i in range(0, len(allresourcepool)):
                myresource = []
                id = allresourcepool[i].id
                name = allresourcepool[i].name
                if i == 0:
                    allresource = ComputerResource.objects.exclude(state="9").filter(pool_id=id)
                    if (len(allresource) > 0):
                        for resource in allresource:
                            resourceid = resource.id
                            resourcename = resource.name
                            myresource.append({"id": resourceid, "name": resourcename})

                result.append({"id": id, "name": name, "myresource": myresource})
        return HttpResponse(json.dumps({"data": result}))


def computerresourcedatafordrill(request):
    if request.user.is_authenticated():
        result = []
        id = request.POST.get('id', '')
        allresource = ComputerResource.objects.exclude(state="9").filter(pool_id=id)
        if (len(allresource) > 0):
            for resource in allresource:
                resourceid = resource.id
                resourcename = resource.name
                result.append({"id": resourceid, "name": resourcename})
        return HttpResponse(json.dumps({"data": result}))


def computerresourcesave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            id = request.POST.get('id', '')
            name = request.POST.get('name', '')
            poolid = request.POST.get('poolid', '')
            description = request.POST.get('description', '')

            ip = request.POST.get('ip', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')

            cpu = request.POST.get('cpu', '')
            memory = request.POST.get('memory', '')

            disk1_size = request.POST.get('disk1_size', '')
            disk2_size = request.POST.get('disk2_size', '')
            disk3_size = request.POST.get('disk3_size', '')
            disk4_size = request.POST.get('disk4_size', '')
            disk5_size = request.POST.get('disk5_size', '')
            disk6_size = request.POST.get('disk6_size', '')

            disk1_name = request.POST.get('disk1_name', '')
            disk2_name = request.POST.get('disk2_name', '')
            disk3_name = request.POST.get('disk3_name', '')
            disk4_name = request.POST.get('disk4_name', '')
            disk5_name = request.POST.get('disk5_name', '')
            disk6_name = request.POST.get('disk6_name', '')

            disk1_type = request.POST.get('disk1_type', '')
            disk2_type = request.POST.get('disk2_type', '')
            disk3_type = request.POST.get('disk3_type', '')
            disk4_type = request.POST.get('disk4_type', '')
            disk5_type = request.POST.get('disk5_type', '')
            disk6_type = request.POST.get('disk6_type', '')

            try:
                id = int(id)
            except:
                raise Http404()
            try:
                poolid = int(poolid)
            except:
                raise Http404()
            if id == 0:
                allresource = ComputerResource.objects.filter(name=name)
                if (len(allresource) > 0):
                    result = u"主机资源名称" + name + u'已存在。'
                else:
                    resource = ComputerResource()
                    resource.name = name
                    mypoll = ResourcePool.objects.get(id=poolid)
                    resource.pool = mypoll
                    resource.description = description

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'CERT_LIST', None)
                    root = dom.documentElement
                    nameE = dom.createElement('CERT')
                    nameE.setAttribute("ip", ip)  # 增加属性
                    nameE.setAttribute("username", username)  # 增加属性
                    nameE.setAttribute("password", password)  # 增加属性
                    root.appendChild(nameE)
                    resource.certificate = dom.toxml()

                    dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                    root = dom1.documentElement
                    root.setAttribute("cpu", cpu)
                    root.setAttribute("memory", memory)
                    if not disk1_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk1_size)  # 增加属性
                        nameE.setAttribute("name", disk1_name)  # 增加属性
                        nameE.setAttribute("type", disk1_type)  # 增加属性
                        root.appendChild(nameE)
                    if not disk2_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk2_size)  # 增加属性
                        nameE.setAttribute("name", disk2_name)  # 增加属性
                        nameE.setAttribute("type", disk2_type)  # 增加属性
                        root.appendChild(nameE)
                    if not disk3_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk3_size)  # 增加属性
                        nameE.setAttribute("name", disk3_name)  # 增加属性
                        nameE.setAttribute("type", disk3_type)  # 增加属性
                        root.appendChild(nameE)
                    if not disk4_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk4_size)  # 增加属性
                        nameE.setAttribute("name", disk4_name)  # 增加属性
                        nameE.setAttribute("type", disk4_type)  # 增加属性
                        root.appendChild(nameE)
                    if not disk5_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk5_size)  # 增加属性
                        nameE.setAttribute("name", disk5_name)  # 增加属性
                        nameE.setAttribute("type", disk5_type)  # 增加属性
                        root.appendChild(nameE)
                    if not disk6_size == '':
                        nameE = dom.createElement('DISK')
                        nameE.setAttribute("size", disk6_size)  # 增加属性
                        nameE.setAttribute("name", disk6_name)  # 增加属性
                        nameE.setAttribute("type", disk6_type)  # 增加属性
                        root.appendChild(nameE)
                    resource.specifications = dom1.toxml()

                    resource.state = "0"
                    resource.creatdate = datetime.datetime.now()
                    resource.updatedate = datetime.datetime.now()
                    resource.save()
                    result = "保存成功。"
            else:
                allresource = ComputerResource.objects.filter(id=id)
                if (len(allresource) > 0):
                    allresource1 = ComputerResource.objects.filter(name=name).exclude(id=id)
                    if (len(allresource1) > 0):
                        result = u"主机资源名称" + name + u'已存在。'
                    else:
                        resource = allresource[0]
                        resource.name = name
                        mypoll = ResourcePool.objects.get(id=poolid)
                        resource.pool = mypoll
                        resource.description = description

                        impl = xml.dom.minidom.getDOMImplementation()
                        dom = impl.createDocument(None, 'CERT_LIST', None)
                        root = dom.documentElement
                        nameE = dom.createElement('CERT')
                        nameE.setAttribute("ip", ip)  # 增加属性
                        nameE.setAttribute("username", username)  # 增加属性
                        nameE.setAttribute("password", password)  # 增加属性
                        root.appendChild(nameE)
                        resource.certificate = dom.toxml()

                        dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                        root = dom1.documentElement
                        root.setAttribute("cpu", cpu)
                        root.setAttribute("memory", memory)

                        if not disk1_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk1_size)  # 增加属性
                            nameE.setAttribute("name", disk1_name)  # 增加属性
                            nameE.setAttribute("type", disk1_type)  # 增加属性
                            root.appendChild(nameE)
                        if not disk2_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk2_size)  # 增加属性
                            nameE.setAttribute("name", disk2_name)  # 增加属性
                            nameE.setAttribute("type", disk2_type)  # 增加属性
                            root.appendChild(nameE)
                        if not disk3_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk3_size)  # 增加属性
                            nameE.setAttribute("name", disk3_name)  # 增加属性
                            nameE.setAttribute("type", disk3_type)  # 增加属性
                            root.appendChild(nameE)
                        if not disk4_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk4_size)  # 增加属性
                            nameE.setAttribute("name", disk4_name)  # 增加属性
                            nameE.setAttribute("type", disk4_type)  # 增加属性
                            root.appendChild(nameE)
                        if not disk5_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk5_size)  # 增加属性
                            nameE.setAttribute("name", disk5_name)  # 增加属性
                            nameE.setAttribute("type", disk5_type)  # 增加属性
                            root.appendChild(nameE)
                        if not disk6_size == '':
                            nameE = dom.createElement('DISK')
                            nameE.setAttribute("size", disk6_size)  # 增加属性
                            nameE.setAttribute("name", disk6_name)  # 增加属性
                            nameE.setAttribute("type", disk6_type)  # 增加属性
                            root.appendChild(nameE)
                        resource.specifications = dom1.toxml()

                        resource.updatedate = datetime.datetime.now()
                        resource.save()
                        result = "保存成功。"
                else:
                    result = "数据异常。"
            return HttpResponse(result)


def computerresourcedel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            myresource = ComputerResource.objects.get(id=id)
            myresource.name = myresource.name + u"(已删除)"
            myresource.state = "9"
            myresource.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def vmresource(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        return render(request, 'vmresource.html', {'username': request.user.userinfo.fullname, "vmresourcepage": True})
    else:
        return HttpResponseRedirect("/login")


def getvmresourcelist(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        allresource = VmResource.objects.exclude(state="9")
        result = []
        pool_id = request.POST.get("pool_id", '')
        resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
        certificate = resourcepool.certificate
        # 从资源池中获取certificate,并获取ip,user,password
        doc = parseString(certificate)
        ip = ""
        username = ""
        password = ""
        for node in doc.getElementsByTagName("CERT_LIST"):
            for hostnode in node.getElementsByTagName("CERT"):
                ip = hostnode.getAttribute("ip")
                username = hostnode.getAttribute("username")
                password = hostnode.getAttribute("password")
                datacenter = hostnode.getAttribute("datacenter")
                cluster = hostnode.getAttribute("cluster")

        vm_api = VM_API(ip, username, password)
        vmlist = vm_api.getvmlist(datacenter, cluster)

        for num, vm in enumerate(vmlist):
            vm_info_dict = {
                "id": num,
                "vm_name": vm['vmname'],
                "cpu": vm['cpu'],
                "memory": vm['memory'],
                "disk": vm['capacity'],
                "uuid": vm['uuid'],
            }

            result.append(vm_info_dict)
        return HttpResponse(json.dumps({"data": result}))


def vmresourcedata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresource = VmResource.objects.exclude(state="9").filter(vm_type='模板虚机')
        if (len(allresource) > 0):
            for resource in allresource:
                id = resource.id
                name = resource.name
                pool_id = resource.pool_id
                specifications = resource.specifications
                description = resource.description
                template_name = resource.template_name  # ...对应的name
                system = resource.system
                uuid = resource.uuid

                vmlist = VmResource.objects.exclude(state="9").exclude(vm_type='模板虚机').filter(template_id=id)
                vm_num = len(vmlist)

                resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
                certificate = resourcepool.certificate
                pool_name = resourcepool.name
                # 从资源池中获取certificate,并获取ip,user,password

                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                cert_name = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                        datacenter = hostnode.getAttribute("datacenter")
                        cluster = hostnode.getAttribute("cluster")
                vm_api = VM_API(ip, username, password)
                vmlist = vm_api.getvmlist(datacenter, cluster, None, name)
                state_tag = """<i class="fa fa-stop fa-2x" style="color:#ff0000;font-size:25px" title="已停止"></i>"""
                for num, vm in enumerate(vmlist):
                    if vm['vmname'] == name:
                        state = vm["state"]
                        if state == "poweredOn":
                            state_tag = """<i class="fa fa-play fa-2" style="color:#00CC00;font-size:25px" title="运行中"></i>"""
                        else:
                            state_tag = """<i class="fa fa-stop fa-2" style="color:#ff0000;font-size:25px" title="已停止"></i>"""

                doc2 = parseString(specifications)
                for node in doc2.getElementsByTagName("SPEC_LIST"):
                    cpu = node.getAttribute("cpu")
                    memory = node.getAttribute("memory")
                    disk = node.getAttribute("disk")
                print("result", result)
                result.append(
                    {"id": id, "name": name, "description": description,
                     "cpu": cpu, "memory": memory,
                     "disks": disk, "template_name": template_name, "vm_num": vm_num, "state_tag": state_tag,
                     "system": system, "pool_id": pool_id, "pool_name": pool_name, "uuid": uuid})
        return HttpResponse(json.dumps({"data": result}))


def vmresourcepooldata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.filter(type="虚机资源").exclude(state="9")
        if (len(allresourcepool) > 0):
            for resourcepool in allresourcepool:
                id = resourcepool.id
                name = resourcepool.name
                type = resourcepool.type
                supplier = resourcepool.supplier
                certificate = resourcepool.certificate
                description = resourcepool.description
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                result.append({"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                               "ip": ip, "username": username, "password": password})
        return HttpResponse(json.dumps({"data": result}))


def vmresourcepooldatafordrill(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9").filter(type="虚机资源")
        if (len(allresourcepool) > 0):
            for i in range(0, len(allresourcepool)):
                myresource = []
                id = allresourcepool[i].id
                name = allresourcepool[i].name
                if i == 0:
                    allresource = VmResource.objects.exclude(state="9").filter(pool_id=id)
                    if (len(allresource) > 0):
                        for resource in allresource:
                            resourceid = resource.id
                            resourcename = resource.name
                            myresource.append({"id": resourceid, "name": resourcename})

                result.append({"id": id, "name": name, "myresource": myresource})
        return HttpResponse(json.dumps({"data": result}))


def vmresourcedatafordrill(request):
    if request.user.is_authenticated():
        result = []
        # id = request.POST.get('id', '')
        allresource = VmResource.objects.exclude(state="9")
        if (len(allresource) > 0):
            for resource in allresource:
                resourceid = resource.id
                resourcename = resource.name
                result.append({"id": resourceid, "name": resourcename})
        return HttpResponse(json.dumps({"data": result}))


def vmresourcesave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            # clone param
            datacenter = request.POST.get('datacenter', '')
            cluster = request.POST.get('cluster', '')
            instancename = request.POST.get('instancename', '')
            currentvm = request.POST.get('currentvm', '')
            clone_tag = request.POST.get('clone_tag', '')
            template_id = request.POST.get('template_id', '')

            id = request.POST.get('id', '')
            if clone_tag:
                vm_name = request.POST.get('currentvm', '')
            else:
                vm_name = request.POST.get('name', '')
            pool_id = request.POST.get('poolid', '')

            cpu = request.POST.get('cpu', '')
            memory = request.POST.get('memory', '')
            disk = request.POST.get('disk', '')

            template = request.POST.get('template', '')
            description = request.POST.get('description', '')
            system = request.POST.get('system')

            uuid = request.POST.get('uuid')

            try:
                id = int(id)
            except:
                raise Http404()

            if id == 0:
                allresource = VmResource.objects.filter(name=vm_name)
                if (len(allresource) > 0):
                    result = u"虚机资源名称" + vm_name + u'已存在。'
                else:
                    resource = VmResource()
                    resource.description = description

                    resource.pool_id = pool_id

                    if clone_tag:
                        resource.template_name = instancename
                        resource.vm_type = "克隆虚机"
                        resource.name = currentvm
                        resource.template_id = template_id
                    else:
                        resource.template_name = template
                        resource.vm_type = "模板虚机"
                        resource.name = vm_name
                    resource.system = system
                    resource.uuid = uuid

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                    root = dom1.documentElement
                    root.setAttribute("cpu", cpu)
                    root.setAttribute("memory", memory)
                    root.setAttribute("disk", disk)
                    root.setAttribute("datacenter", datacenter)
                    root.setAttribute("cluster", cluster)

                    resource.specifications = dom1.toxml()

                    resource.state = "0"
                    resource.creatdate = datetime.datetime.now()
                    resource.updatedate = datetime.datetime.now()

                    resource.save()
                    result = "保存成功。"

            else:
                allresource = VmResource.objects.filter(id=id)
                if (len(allresource) > 0):
                    allresource1 = VmResource.objects.filter(name=vm_name).exclude(id=id)
                    if (len(allresource1) > 0):
                        result = u"虚机资源名称" + vm_name + u'已存在。'
                    else:
                        resource = allresource[0]
                        resource.name = vm_name
                        resource.template_name = template
                        resource.system = system
                        resource.uuid = uuid
                        resource.pool_id = pool_id
                        resource.description = description

                        impl = xml.dom.minidom.getDOMImplementation()
                        dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                        root = dom1.documentElement
                        root.setAttribute("cpu", cpu)
                        root.setAttribute("memory", memory)
                        root.setAttribute("disk", disk)

                        resource.specifications = dom1.toxml()

                        resource.updatedate = datetime.datetime.now()
                        resource.save()
                        result = "保存成功。"
                else:
                    result = "数据异常。"
            return HttpResponse(result)


def vmresourcedel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            myresource = VmResource.objects.get(id=id)
            myresource.name = myresource.name + u"(已删除)"
            myresource.state = "9"
            myresource.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def vmresourcedestroy(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()

            pool_id = request.POST.get("pool_id", "")
            name = request.POST.get("name", "")
            uuid = request.POST.get("uuid", "")
            if pool_id:
                resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
                certificate = resourcepool.certificate
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")

                vm_api = VM_API(ip, username, password)
                ip = request.POST.get("ip", "")
                try:
                    vm_api.destroy_vm(uuid, name, ip)
                except:
                    return HttpResponse(0)
                myresource = VmResource.objects.get(id=id)
                myresource.name = myresource.name + u"(已删除)"
                myresource.state = "9"
                myresource.save()

                return HttpResponse(1)
        else:
            return HttpResponse(0)


def vmlistmanage(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        return render(request, 'vmlistmanage.html',
                      {'username': request.user.userinfo.fullname, "vmlistmanagepage": True})


def vmlistmanagedata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresource = VmResource.objects.exclude(state="9").exclude(vm_type='模板虚机')
        if (len(allresource) > 0):
            for resource in allresource:
                id = resource.id
                name = resource.name
                pool_id = resource.pool_id
                specifications = resource.specifications
                description = resource.description
                instance_name = resource.template_name  # ...对应的name
                system = resource.system
                template_id = resource.template_id
                template_name = resource.template.name
                template_template_name = resource.template.template_name
                template_uuid = resource.template.uuid
                uuid = resource.uuid

                resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
                certificate = resourcepool.certificate
                pool_name = resourcepool.name
                # 从资源池中获取certificate,并获取ip,user,password

                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                cert_name = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                        datacenter = hostnode.getAttribute("datacenter")
                        cluster = hostnode.getAttribute("cluster")

                vm_api = VM_API(ip, username, password)
                vmlist = vm_api.getvmlist(datacenter, cluster, None, name)
                state_tag = """<i class="fa fa-stop fa-2x" style="color:#ff0000;font-size:25px" title="已停止"></i>"""
                for num, vm in enumerate(vmlist):
                    if vm['vmname'] == name:
                        state = vm["state"]
                        if state == "poweredOn":
                            state_tag = """<i class="fa fa-play fa-2" style="color:#00CC00;font-size:25px" title="运行中"></i>"""
                        else:
                            state_tag = """<i class="fa fa-stop fa-2x" style="color:#ff0000;font-size:25px" title="已停止"></i>"""

                doc2 = parseString(specifications)
                for node in doc2.getElementsByTagName("SPEC_LIST"):
                    cpu = node.getAttribute("cpu")
                    memory = node.getAttribute("memory")
                    disk = node.getAttribute("disk")
                    vmip = node.getAttribute("vmip")
                    hostname = node.getAttribute("hostname")
                    clone = node.getAttribute("clone")

                result.append(
                    {"id": id, "name": name, "description": description,
                     "cpu": cpu, "memory": memory, "datacenter": datacenter, "cluster": cluster, "ip": vmip,
                     "hostname": hostname,
                     "disks": disk, "instance_name": instance_name, "template_id": template_id, "clone": clone,
                     "template_name": template_name, "template_template_name": template_template_name,
                     "template_uuid": template_uuid, "state_tag": state_tag, "system": system, "pool_id": pool_id,
                     "pool_name": pool_name, "uuid": uuid})
        return HttpResponse(json.dumps({"data": result}))


def getvmtemplate(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        id = request.POST.get('id', '')
        if id != "0":
            result = []
            allresource = VmResource.objects.exclude(state="9").filter(vm_type='模板虚机')
            if (len(allresource) > 0):
                for resource in allresource:
                    id = resource.id
                    name = resource.name
                    pool_id = resource.pool_id
                    specifications = resource.specifications
                    description = resource.description
                    template_name = resource.template_name  # ...对应的name
                    system = resource.system
                    uuid = resource.uuid

                    resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
                    certificate = resourcepool.certificate
                    pool_name = resourcepool.name

                    doc1 = parseString(certificate)
                    for node in doc1.getElementsByTagName("CERT_LIST"):
                        for hostnode in node.getElementsByTagName("CERT"):
                            datacenter = hostnode.getAttribute("datacenter")
                            cluster = hostnode.getAttribute("cluster")

                    doc2 = parseString(specifications)
                    for node in doc2.getElementsByTagName("SPEC_LIST"):
                        cpu = node.getAttribute("cpu")
                        memory = node.getAttribute("memory")
                        disk = node.getAttribute("disk")

                    result.append(
                        {"id": id, "name": name, "description": description,
                         "cpu": cpu, "memory": memory, "system": system,
                         "disks": disk, "template_name": template_name, "system": system, "pool_id": pool_id,
                         "pool_name": pool_name, "uuid": uuid, "datacenter": datacenter, "cluster": cluster})
        else:
            result = []
            template_name = request.POST.get("template_name", "")
            resource = VmResource.objects.exclude(state="9").filter(vm_type='模板虚机').filter(template_name=template_name)[
                0]
            id = resource.id
            name = resource.name
            specifications = resource.specifications
            description = resource.description
            template_name = resource.template_name  # ...对应的name
            system = resource.system
            uuid = resource.uuid
            pool_id = resource.pool_id
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate

            doc1 = parseString(certificate)
            for node in doc1.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    datacenter = hostnode.getAttribute("datacenter")
                    cluster = hostnode.getAttribute("cluster")

            doc2 = parseString(specifications)
            for node in doc2.getElementsByTagName("SPEC_LIST"):
                cpu = node.getAttribute("cpu")
                memory = node.getAttribute("memory")
                disk = node.getAttribute("disk")

            result.append({"id": id, "name": name, "description": description,
                           "cpu": cpu, "memory": memory,
                           "disks": disk, "template_name": template_name, "system": system,
                           "uuid": uuid, "pool_id": pool_id, "datacenter": datacenter, "cluster": cluster})
        return HttpResponse(json.dumps({"data": result}))


def get_dc(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        pool_id = request.POST.get("poolid", "")
        clusterlist = []
        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
            vm_api = VM_API(ip, username, password)
            clusterlist = vm_api.getdatacenterlist()
        return JsonResponse({"data": clusterlist})


def get_cluster(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        clusterlist = []
        pool_id = request.POST.get("poolid", "")
        datacenter = request.POST.get("datacenter", "")
        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
            vm_api = VM_API(ip, username, password)
            clusterlist = vm_api.getclusterlist(datacenter)
        return JsonResponse({"data": clusterlist})


def clonevm(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = {}
            # clone param
            datacenter = request.POST.get('datacenter', '')
            cluster = request.POST.get('cluster', '')
            instancename = request.POST.get('instancename', '')
            currentvm = request.POST.get('currentvm', '')
            template_id = request.POST.get('template_id', '')

            id = request.POST.get('id', '')
            vm_name = request.POST.get('currentvm', '')
            name = request.POST.get('name', '')
            pool_id = request.POST.get('poolid', '')

            cpu = request.POST.get('cpu', '')
            memory = request.POST.get('memory', '')
            disk = request.POST.get('disk', '')
            description = request.POST.get('description', '')
            system = request.POST.get('system')

            try:
                id = int(id)
            except:
                raise Http404()

            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")

            if id == 0:
                allresource = VmResource.objects.filter(name=vm_name)
                if (len(allresource) > 0):
                    result = u"新虚机名称" + vm_name + u'已存在。'
                else:
                    vm_api = VM_API(ip, username, password)
                    task = vm_api.clone_vm(name, vm_name, datacenter, cluster)
                    if task:
                        resource = VmResource()
                        resource.description = description

                        resource.pool_id = pool_id
                        resource.template_name = instancename
                        resource.vm_type = "实例虚机"
                        resource.name = currentvm
                        resource.template_id = template_id
                        resource.system = system

                        impl = xml.dom.minidom.getDOMImplementation()
                        dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                        root = dom1.documentElement
                        root.setAttribute("cpu", cpu)
                        root.setAttribute("memory", memory)
                        root.setAttribute("disk", disk)
                        root.setAttribute("datacenter", datacenter)
                        root.setAttribute("cluster", cluster)
                        root.setAttribute("clone", "0")
                        root.setAttribute("clonetaskid", task.info.key)

                        resource.specifications = dom1.toxml()

                        resource.state = "0"
                        resource.creatdate = datetime.datetime.now()
                        resource.updatedate = datetime.datetime.now()

                        resource.save()
                        result = {"value": "1", "id": resource.id, "text": u"克隆启动成功。"}

                        # 流程中克隆，保存步骤信息
                        if 'steprunid' in request.POST:
                            steprunid = request.POST.get('steprunid', '')
                            try:
                                steprunid = int(steprunid)
                            except:
                                raise Http404()
                            steprun = StepRun.objects.filter(id=steprunid)
                            if len(steprun) <= 0:
                                result["res"] = '执行失败，该步骤配置异常。'
                            else:
                                steprun[0].state = "RUN"
                                steprun[0].parameter = "<clonevmid>" + str(resource.id) + "</clonevmid>"
                                steprun[0].save()
                    else:
                        result = {"value": "0", "text": u"克隆失败。"}
            else:
                result = {"value": "0", "text": u"克隆失败。"}
            return HttpResponse(json.dumps(result))


def get_progress(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        pool_id = request.POST.get("poolid", "")
        template_name = request.POST.get("name", "")
        id = request.POST.get("id", "")
        name = request.POST.get('currentvm', '')
        try:
            id = int(id)
        except:
            raise Http404()
        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
                    datacenter = hostnode.getAttribute("datacenter")
                    cluster = hostnode.getAttribute("cluster")
            vm_api = VM_API(ip, username, password)
            vmlist = vm_api.getvmlist(datacenter, cluster, None, template_name)
            progress = "0"
            state = "2"
            uuid = ""
            finished = True
            if len(vmlist) > 0:
                vm = vmlist[0]
                for task in vm["task"]:
                    if task["descriptionId"] == "VirtualMachine.clone":
                        resource = VmResource.objects.filter(id=id)
                        if (len(resource) > 0):

                            specifications = resource[0].specifications

                            doc2 = parseString(specifications)
                            for node in doc2.getElementsByTagName("SPEC_LIST"):
                                clonetaskid = node.getAttribute("clonetaskid")

                                if clonetaskid == task["key"] and task["state"] != "success":
                                    progress = task["progress"]
                                    finished = False
            if finished:
                state = "3"
                resource = VmResource.objects.filter(id=id)
                if (len(resource) > 0):
                    specifications = resource[0].specifications
                    name = resource[0].name
                    doc2 = parseString(specifications)
                    for node in doc2.getElementsByTagName("SPEC_LIST"):
                        node.setAttribute("clone", "1")
                        specifications = doc2.toxml()
                    newvmlsit = vm_api.getvmlist(datacenter, cluster, None, name)
                    if len(newvmlsit) > 0:
                        resource[0].uuid = newvmlsit[0]["uuid"]
                        resource[0].specifications = specifications
                        resource[0].save()

                        uuid = newvmlsit[0]["uuid"]
                        state = "3"
        result = {"progress": progress, "state": state, "uuid": uuid}
        return HttpResponse(json.dumps(result))


def vm_ipsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        uuid = request.POST.get("uuid", "")
        path = request.POST.get("path", "")
        vmip = request.POST.get("ip", "")
        mask = request.POST.get("mask", "")
        gateway = request.POST.get("gateway", "")
        dns = request.POST.get("dns", "")
        vmuser = request.POST.get("user", "")
        vmpassword = request.POST.get("password", "")
        id = request.POST.get("id", "")
        try:
            id = int(id)
        except:
            raise Http404()

        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
                    datacenter = hostnode.getAttribute("datacenter")
                    cluster = hostnode.getAttribute("cluster")
            vm_api = VM_API(ip, username, password)
            if vm_api.execute_program(uuid, vmuser, vmpassword, path, vmip + " " + mask + " " + gateway + " " + dns):
                resource = VmResource.objects.filter(id=id)
                if (len(resource) > 0):
                    specifications = resource[0].specifications
                    doc2 = parseString(specifications)
                    for node in doc2.getElementsByTagName("SPEC_LIST"):
                        node.setAttribute("vmip", vmip)
                        specifications = doc2.toxml()
                        resource[0].specifications = specifications
                        resource[0].save()
                result = {"value": "1", "text": "执行成功"}
            else:
                result = {"value": "0", "text": vm_api.msg}

        return HttpResponse(json.dumps(result))


def vm_hostsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        uuid = request.POST.get("uuid", "")
        path = request.POST.get("path", "")
        hostname = request.POST.get("hostname", "")
        vmuser = request.POST.get("user", "")
        vmpassword = request.POST.get("password", "")
        id = request.POST.get("id", "")
        try:
            id = int(id)
        except:
            raise Http404()

        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
                    datacenter = hostnode.getAttribute("datacenter")
                    cluster = hostnode.getAttribute("cluster")
            vm_api = VM_API(ip, username, password)
            if vm_api.execute_program(uuid, vmuser, vmpassword, path, hostname):
                resource = VmResource.objects.filter(id=id)
                if (len(resource) > 0):
                    specifications = resource[0].specifications
                    doc2 = parseString(specifications)
                    for node in doc2.getElementsByTagName("SPEC_LIST"):
                        node.setAttribute("hostname", hostname)
                        specifications = doc2.toxml()
                        resource[0].specifications = specifications
                        resource[0].save()
                result = {"value": "1", "text": "执行成功"}
            else:
                result = {"value": "0", "text": vm_api.msg}
        return HttpResponse(json.dumps(result))


def vm_disksave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        uuid = request.POST.get("uuid", "")
        disksize = request.POST.get("disksize", "")
        disktype = request.POST.get("disktype", "")
        selectdisk = request.POST.get("selectdisk", "")
        path = request.POST.get("path", "")
        vmuser = request.POST.get("user", "")
        vmpassword = request.POST.get("password", "")
        name = request.POST.get("name", "")
        id = request.POST.get("id", "")
        try:
            id = int(id)
        except:
            raise Http404()
        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            size = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
            vm_api = VM_API(ip, username, password)

            try:
                disknum = vm_api.add_disk(name, disktype, disksize, uuid)  # disknum
                if disknum == -9:
                    result = {"value": "0", "text": "超时！！！", "size": size}
                else:
                    # initialize disk
                    if vm_api.execute_program(uuid, vmuser, vmpassword, path, str(disknum) + " " + selectdisk):
                        resource = VmResource.objects.filter(id=id)
                        if (len(resource) > 0):
                            specifications = resource[0].specifications
                            doc2 = parseString(specifications)
                            for node in doc2.getElementsByTagName("SPEC_LIST"):
                                oldsize = 0
                                newsize = 0
                                try:
                                    oldsize = int(node.getAttribute("disk"))
                                except:
                                    pass
                                try:
                                    newsize = int(disksize)
                                except:
                                    pass
                                size = str(oldsize + newsize)

                                node.setAttribute("disk", size)
                                specifications = doc2.toxml()
                                resource[0].specifications = specifications
                                resource[0].save()
                        result = {"value": "1", "text": "执行成功", "size": size}
                    else:
                        result = {"value": "0", "text": "执行失败", "size": size}
            except:
                result = {"value": "0", "text": vm_api.msg, "size": size}
        return HttpResponse(json.dumps(result))


def vm_installcvsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        uuid = request.POST.get("uuid", "")
        path = request.POST.get("path", "")
        hostname = request.POST.get("hostname", "")
        vmuser = request.POST.get("user", "")
        vmpassword = request.POST.get("password", "")

        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id)).filter(
            clientName=hostname + "." + request.user.username)
        if (len(allhost) > 0):
            result = {"value": "0", "text": u"主机名" + hostname + "." + request.user.usernamee + u'已注册,请勿重复安装。'}

        else:
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            clientInfo = cvAPI.getClientInfo(hostname + "." + request.user.username)
            if clientInfo:
                result = {"value": "0", "text": u"主机" + hostname + "." + request.user.username + u'已安装客户端,请勿重复安装。'}
            else:
                if pool_id:
                    resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
                    certificate = resourcepool.certificate
                    doc = parseString(certificate)
                    ip = ""
                    username = ""
                    password = ""
                    for node in doc.getElementsByTagName("CERT_LIST"):
                        for hostnode in node.getElementsByTagName("CERT"):
                            ip = hostnode.getAttribute("ip")
                            username = hostnode.getAttribute("username")
                            password = hostnode.getAttribute("password")
                            datacenter = hostnode.getAttribute("datacenter")
                            cluster = hostnode.getAttribute("cluster")
                    vm_api = VM_API(ip, username, password)
                    if vm_api.execute_program(uuid, vmuser, vmpassword, path, request.user.username):
                        result = {"value": "1", "text": "执行成功"}
                    else:
                        result = {"value": "0", "text": vm_api.msg}

        return HttpResponse(json.dumps(result))


def registercvsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        hostname = request.POST.get("hostname", "")

        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id)).filter(
            clientName=hostname + "." + request.user.username)
        if (len(allhost) > 0):
            result = {"value": "0", "text": u"主机名" + hostname + u'已注册,请勿重复注册。'}

        else:
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            clientInfo = cvAPI.getClientInfo(hostname + "." + request.user.username)
            if not clientInfo:
                result = {"value": "0", "text": u"主机" + hostname + u'未安装客户端,请先安装commvalut客户端。'}
            else:
                agentTypeList = "<agentTypeList>"
                for node in clientInfo["agentList"]:
                    if node["agentType"] == "File System":
                        agentTypeList += "<agentType>FILESYSTEM</agentType>"
                    else:
                        if node["agentType"] == "Oracle":
                            agentTypeList += "<agentType>ORACLE</agentType>"
                        else:
                            if node["agentType"] == "SQL Server":
                                agentTypeList += "<agentType>MSSQL</agentType>"
                            else:
                                agentTypeList += "<agentType>" + node["agentType"] + "</agentType>"
                agentTypeList += "</agentTypeList>"
                clientID = clientInfo["clientId"]

                try:
                    clientID = int(clientID)
                except:
                    clientID = 0
                platform = clientInfo["platform"]["platform"]

                result = {}
                user = request.user
                if user is not None and user.is_active:
                    try:
                        clienthost = ClientHost()
                        clienthost.clientGUID = uuid.uuid1()
                        clienthost.clientName = hostname
                        clienthost.owernID = user.userinfo.userGUID
                        clienthost.hostType = "physical box"
                        clienthost.clientID = clientID
                        clienthost.agentTypeList = agentTypeList
                        clienthost.status = "0"
                        clienthost.platform = platform
                        clienthost.appGroup = "缺省"
                        clienthost.installTime = datetime.datetime.now()
                        clienthost.save()
                        result = {"value": "1", "text": u"注册成功。"}
                    except:
                        result = {"value": "0", "text": u"注册失败。"}

        return HttpResponse(json.dumps(result))


def rebootvm(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        pool_id = request.POST.get("poolid", '')
        uuid = request.POST.get("uuid", '')
        hostname = request.POST.get("hostname", '')
        resourcepool = ResourcePool.objects.filter(id=int(pool_id))[0]
        certificate = resourcepool.certificate

        doc = parseString(certificate)
        ip = ""
        username = ""
        password = ""
        for node in doc.getElementsByTagName("CERT_LIST"):
            for hostnode in node.getElementsByTagName("CERT"):
                ip = hostnode.getAttribute("ip")
                username = hostnode.getAttribute("username")
                password = hostnode.getAttribute("password")
        vm_api = VM_API(ip, username, password)
        try:
            vmname, powerState = vm_api.reboot_vm(uuid, hostname, None)
            result = {"text": "重启成功"}
        except:
            result = {"text": "启动失败"}
        return JsonResponse(result)


def poweronvm(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        name = request.POST.get("currentvm", "")

        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")

            vm_api = VM_API(ip, username, password)
            try:
                vm_api.power_on_vm(name)
            except:
                result = {"text": "开机失败"}
            result = {"text": "开机成功"}
        return JsonResponse(result)


def shutdownvm(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        pool_id = request.POST.get("poolid", "")
        name = request.POST.get("currentvm", "")

        if pool_id:
            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")

            vm_api = VM_API(ip, username, password)
            try:
                vm_api.power_off_vm(name)
            except:
                result = {"text": "关机失败"}
            result = {"text": "关机成功"}
        return JsonResponse(result)


def get_vm_state(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        pool_id = request.POST.get('poolid', '')
        name = request.POST.get('name', '')
        resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
        certificate = resourcepool.certificate

        doc = parseString(certificate)
        ip = ""
        username = ""
        password = ""
        for node in doc.getElementsByTagName("CERT_LIST"):
            for hostnode in node.getElementsByTagName("CERT"):
                ip = hostnode.getAttribute("ip")
                username = hostnode.getAttribute("username")
                password = hostnode.getAttribute("password")
                datacenter = hostnode.getAttribute("datacenter")
                cluster = hostnode.getAttribute("cluster")
        vm_api = VM_API(ip, username, password)
        vmlist = vm_api.getvmlist(datacenter, cluster, None, name)
        state = ''
        for vm in vmlist:
            state = vm['state']
        result = {
            "state": state,
        }
        return JsonResponse(result)


def get_dc_clt_from_pool(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        pool_id = request.POST.get("poolid", "")
        resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
        certificate = resourcepool.certificate
        doc = parseString(certificate)
        datacenter = ""
        cluster = ""
        for node in doc.getElementsByTagName("CERT_LIST"):
            for hostnode in node.getElementsByTagName("CERT"):
                datacenter = hostnode.getAttribute("datacenter")
                cluster = hostnode.getAttribute("cluster")
        result = {
            "datacenter": datacenter,
            "cluster": cluster,
        }
        return JsonResponse(result)


def backupresource(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        return render(request, 'backupresource.html',
                      {'username': request.user.userinfo.fullname, "backupresourcepage": True})
    else:
        return HttpResponseRedirect("/login")


def backupresourcedata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresource = BackupResource.objects.exclude(state="9")
        if (len(allresource) > 0):
            for resource in allresource:
                id = resource.id
                name = resource.name
                poolid = resource.pool.id
                poolname = resource.pool.name
                certificate = resource.certificate
                specifications = resource.specifications
                description = resource.description
                state = "空闲"
                if resource.state == "1":
                    state = "已使用"
                doc = parseString(certificate)
                cert_name = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        cert_name = hostnode.getAttribute("name")
                doc2 = parseString(specifications)
                spec_type = ""
                spec_time = ""
                spec_size = ""
                spec_perform = ""

                for node in doc2.getElementsByTagName("SPEC_LIST"):
                    spec_type = node.getAttribute("type")
                    spec_time = node.getAttribute("time")
                    spec_size = node.getAttribute("size")
                    spec_perform = node.getAttribute("perform")
                result.append(
                    {"id": id, "name": name, "poolid": poolid, "poolname": poolname, "description": description,
                     "state": state, "cert_name": cert_name, "spec_type": spec_type, "spec_time": spec_time,
                     "spec_size": spec_size, "spec_perform": spec_perform})
        return HttpResponse(json.dumps({"data": result}))


def backupresourcepooldata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9").filter(type="备份资源")
        if (len(allresourcepool) > 0):
            for resourcepool in allresourcepool:
                id = resourcepool.id
                name = resourcepool.name
                type = resourcepool.type
                supplier = resourcepool.supplier
                certificate = resourcepool.certificate
                description = resourcepool.description
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                result.append({"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                               "ip": ip, "username": username, "password": password})
        return HttpResponse(json.dumps({"data": result}))


def getbackupcert(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            result = []
            if 'id' in request.POST:
                poolid = request.POST.get('poolid', '')
                try:
                    poolid = int(poolid)
                except:
                    raise Http404()

            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            for node in cvAPI.getSPList():
                result.append({"id": node["SPName"], "name": node["SPName"]})

            return HttpResponse(json.dumps(result))


def backupresourcesave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            id = request.POST.get('id', '')
            name = request.POST.get('name', '')
            poolid = request.POST.get('poolid', '')
            description = request.POST.get('description', '')

            spec_type = request.POST.get('spec_type', '')
            spec_time = request.POST.get('spec_time', '')
            spec_size = request.POST.get('spec_size', '')
            spec_perform = request.POST.get('spec_perform', '')

            cert_name = request.POST.get('cert_name', '')

            try:
                id = int(id)
            except:
                raise Http404()
            try:
                poolid = int(poolid)
            except:
                raise Http404()
            if id == 0:
                allresource = BackupResource.objects.filter(name=name)
                if (len(allresource) > 0):
                    result = u"备份资源名称" + name + u'已存在。'
                else:
                    resource = BackupResource()
                    resource.name = name
                    mypoll = ResourcePool.objects.get(id=poolid)
                    resource.pool = mypoll  # ?????
                    resource.description = description

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'CERT_LIST', None)
                    root = dom.documentElement
                    nameE = dom.createElement('CERT')
                    nameE.setAttribute("name", cert_name)  # 增加属性
                    root.appendChild(nameE)
                    resource.certificate = dom.toxml()

                    dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                    root = dom1.documentElement
                    root.setAttribute("type", spec_type)
                    root.setAttribute("time", spec_time)
                    root.setAttribute("size", spec_size)
                    root.setAttribute("perform", spec_perform)
                    resource.specifications = dom1.toxml()

                    resource.state = "0"
                    resource.creatdate = datetime.datetime.now()
                    resource.updatedate = datetime.datetime.now()
                    resource.save()
                    result = "保存成功。"
            else:
                allresource = BackupResource.objects.filter(id=id)
                if (len(allresource) > 0):
                    allresource1 = BackupResource.objects.filter(name=name).exclude(id=id)
                    if (len(allresource1) > 0):
                        result = u"备份资源名称" + name + u'已存在。'
                    else:
                        resource = allresource[0]
                        resource.name = name
                        mypoll = ResourcePool.objects.get(id=poolid)
                        resource.pool = mypoll
                        resource.description = description

                        impl = xml.dom.minidom.getDOMImplementation()
                        dom = impl.createDocument(None, 'CERT_LIST', None)
                        root = dom.documentElement
                        nameE = dom.createElement('CERT')
                        nameE.setAttribute("name", cert_name)  # 增加属性
                        root.appendChild(nameE)
                        resource.certificate = dom.toxml()

                        dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                        root = dom1.documentElement
                        root.setAttribute("type", spec_type)
                        root.setAttribute("time", spec_time)
                        root.setAttribute("size", spec_size)
                        root.setAttribute("perform", spec_perform)
                        resource.specifications = dom1.toxml()

                        resource.updatedate = datetime.datetime.now()
                        resource.save()
                        result = "保存成功。"
                else:
                    result = "数据异常。"
            return HttpResponse(result)


def backupresourcedel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            myresource = BackupResource.objects.get(id=id)
            myresource.name = myresource.name + u"(已删除)"
            myresource.state = "9"
            myresource.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def schduleresource(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        return render(request, 'schduleresource.html',
                      {'username': request.user.userinfo.fullname, "schduleresourcepage": True})
    else:
        return HttpResponseRedirect("/login")


def schduleresourcedata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresource = SchduleResource.objects.exclude(state="9")
        if (len(allresource) > 0):
            for resource in allresource:
                id = resource.id
                name = resource.name
                poolid = resource.pool.id
                poolname = resource.pool.name
                certificate = resource.certificate
                specifications = resource.specifications
                description = resource.description
                state = "空闲"
                if resource.state == "1":
                    state = "已使用"
                doc = parseString(certificate)
                cert_name = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        cert_name = hostnode.getAttribute("name")

                doc2 = parseString(specifications)
                spec_type = ""
                spec_rpo = ""

                for node in doc2.getElementsByTagName("SPEC_LIST"):
                    spec_type = node.getAttribute("type")
                    spec_rpo = node.getAttribute("rpo")
                result.append(
                    {"id": id, "name": name, "poolid": poolid, "poolname": poolname, "description": description,
                     "state": state, "spec_type": spec_type, "spec_rpo": spec_rpo, "cert_name": cert_name})
        return HttpResponse(json.dumps({"data": result}))


def schduleresourcepooldata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allresourcepool = ResourcePool.objects.exclude(state="9").filter(type="计划资源")
        if (len(allresourcepool) > 0):
            for resourcepool in allresourcepool:
                id = resourcepool.id
                name = resourcepool.name
                type = resourcepool.type
                supplier = resourcepool.supplier
                certificate = resourcepool.certificate
                description = resourcepool.description
                doc = parseString(certificate)
                ip = ""
                username = ""
                password = ""
                for node in doc.getElementsByTagName("CERT_LIST"):
                    for hostnode in node.getElementsByTagName("CERT"):
                        ip = hostnode.getAttribute("ip")
                        username = hostnode.getAttribute("username")
                        password = hostnode.getAttribute("password")
                result.append({"id": id, "name": name, "type": type, "supplier": supplier, "description": description,
                               "ip": ip, "username": username, "password": password})
        return HttpResponse(json.dumps({"data": result}))


def getschdulecert(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':

            result = []
            if 'id' in request.POST:
                poolid = request.POST.get('poolid', '')
                try:
                    poolid = int(poolid)
                except:
                    raise Http404()
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            for node in cvAPI.getSchduleList():
                result.append({"id": node["SchduleName"], "name": node["SchduleName"]})
            return HttpResponse(json.dumps(result))


def schduleresourcesave(request):
    if request.user.is_authenticated() and request.session['ispuser']:
        if request.method == 'POST':
            result = ""
            id = request.POST.get('id', '')
            name = request.POST.get('name', '')
            poolid = request.POST.get('poolid', '')
            description = request.POST.get('description', '')

            spec_type = request.POST.get('spec_type', '')
            spec_rpo = request.POST.get('spec_rpo', '')

            cert_name = request.POST.get('cert_name', '')

            try:
                id = int(id)
            except:
                raise Http404()
            try:
                poolid = int(poolid)
            except:
                raise Http404()
            if id == 0:
                allresource = SchduleResource.objects.filter(name=name)
                if (len(allresource) > 0):
                    result = u"计划资源名称" + name + u'已存在。'
                else:
                    resource = SchduleResource()
                    resource.name = name
                    mypoll = ResourcePool.objects.get(id=poolid)
                    resource.pool = mypoll
                    resource.description = description

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'CERT_LIST', None)
                    root = dom.documentElement
                    nameE = dom.createElement('CERT')
                    nameE.setAttribute("name", cert_name)  # 增加属性
                    root.appendChild(nameE)
                    resource.certificate = dom.toxml()

                    dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                    root = dom1.documentElement
                    root.setAttribute("type", spec_type)
                    root.setAttribute("rpo", spec_rpo)
                    resource.specifications = dom1.toxml()

                    resource.state = "0"
                    resource.creatdate = datetime.datetime.now()
                    resource.updatedate = datetime.datetime.now()
                    resource.save()
                    result = "保存成功。"
            else:
                allresource = SchduleResource.objects.filter(id=id)
                if (len(allresource) > 0):
                    allresource1 = SchduleResource.objects.filter(name=name).exclude(id=id)
                    if (len(allresource1) > 0):
                        result = u"计划资源名称" + name + u'已存在。'
                    else:
                        resource = allresource[0]
                        resource.name = name
                        mypoll = ResourcePool.objects.get(id=poolid)
                        resource.pool = mypoll
                        resource.description = description

                        impl = xml.dom.minidom.getDOMImplementation()
                        dom = impl.createDocument(None, 'CERT_LIST', None)
                        root = dom.documentElement
                        nameE = dom.createElement('CERT')
                        nameE.setAttribute("name", cert_name)  # 增加属性
                        root.appendChild(nameE)
                        resource.certificate = dom.toxml()

                        dom1 = impl.createDocument(None, 'SPEC_LIST', None)
                        root = dom1.documentElement
                        root.setAttribute("type", spec_type)
                        root.setAttribute("rpo", spec_rpo)
                        resource.specifications = dom1.toxml()

                        resource.updatedate = datetime.datetime.now()
                        resource.save()
                        result = "保存成功。"
                else:
                    result = "数据异常。"
            return HttpResponse(result)


def schduleresourcedel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            myresource = SchduleResource.objects.get(id=id)
            myresource.name = myresource.name + u"(已删除)"
            myresource.state = "9"
            myresource.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def addPhyClient(request):
    username = request.GET.get('username', '').replace('^', ' ')
    password = request.GET.get('password', '').replace('^', ' ')
    clientName = request.GET.get('clientName', '').replace('^', ' ')
    vendor = request.GET.get('vendor', '').replace('^', ' ')
    zone = request.GET.get('zone', '').replace('^', ' ')

    client = clientName + u'.' + username
    cvToken = CV_RestApi_Token()
    cvToken.login(info)
    cvAPI = CV_API(cvToken)
    clientInfo = cvAPI.getClientInfo(client)
    agentTypeList = "<agentTypeList>"
    for node in clientInfo["agentList"]:
        if node["agentType"] == "File System":
            agentTypeList += "<agentType>FILESYSTEM</agentType>"
        else:
            if node["agentType"] == "Oracle":
                agentTypeList += "<agentType>ORACLE</agentType>"
            else:
                if node["agentType"] == "SQL Server":
                    agentTypeList += "<agentType>MSSQL</agentType>"
                else:
                    agentTypeList += "<agentType>" + node["agentType"] + "</agentType>"
    agentTypeList += "</agentTypeList>"
    clientID = clientInfo["clientId"]

    try:
        clientID = int(clientID)
    except:
        clientID = 0
    platform = clientInfo["platform"]

    result = {}
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        allhost = ClientHost.objects.filter(clientName=clientName + "." + user.username)
        result = {"value": "-9", "text": u"新增失败。"}
        if (len(allhost) > 0):
            result = {"value": "-2", "text": u"主机名称" + clientName + u'已存在。'}
        else:
            try:
                clienthost = ClientHost()
                clienthost.clientGUID = uuid.uuid1()
                clienthost.clientName = clientName + "." + user.username
                clienthost.owernID = user.userinfo.userGUID
                clienthost.hostType = "physical box"
                clienthost.vendor = vendor
                clienthost.zone = zone
                clienthost.clientID = clientID
                clienthost.agentTypeList = agentTypeList
                clienthost.status = "0"
                clienthost.platform = platform
                clienthost.appGroup = "缺省"
                clienthost.installTime = datetime.datetime.now()
                clienthost.save()
                result = {"value": "1", "text": u"新增成功。"}
            except:
                result = {"value": "-9", "text": u"新增失败。"}
    else:
        result = {"value": "-1", "text": u"用户名密码错误。"}
    return HttpResponse(json.dumps(result))


@csrf_exempt
def checkPhyClient(request):
    username = request.GET.get('username', '').replace('^', ' ')
    password = request.GET.get('password', '').replace('^', ' ')
    clientName = request.GET.get('clientName', '').replace('^', ' ')

    result = {}
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        allhost = ClientHost.objects.filter(clientName=clientName + "." + user.username)
        result = {"value": "-9", "text": u"新增失败。"}
        if (len(allhost) > 0):
            result = {"value": "-2", "text": u"主机名称" + clientName + u'已存在。'}
        else:
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            clientList = cvAPI.getClientList()
            for node in clientList:
                if node["clientName"] == clientName + u'.' + username:
                    result = {"value": "-3", "text": clientName + u"已安装，但需重新注册。"}
                    return HttpResponse(json.dumps(result))
            result = {"value": "1", "text": u"允许安装。", "clientName": "test1", "hostName": "test1"}
    else:
        result = {"value": "-1", "text": u"用户名密码错误。"}
    return HttpResponse(json.dumps(result))


def serverconfig(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        cvvendor = Vendor.objects.filter(name='CommVault')
        id = 0
        webaddr = ""
        port = ""
        usernm = ""
        passwd = ""
        if (len(cvvendor) > 0):
            id = cvvendor[0].id
            doc = parseString(cvvendor[0].content)
            try:
                webaddr = (doc.getElementsByTagName("webaddr"))[0].childNodes[0].data
            except:
                pass
            try:
                port = (doc.getElementsByTagName("port"))[0].childNodes[0].data
            except:
                pass
            try:
                usernm = (doc.getElementsByTagName("username"))[0].childNodes[0].data
            except:
                pass
            try:
                passwd = (doc.getElementsByTagName("passwd"))[0].childNodes[0].data
            except:
                pass
        return render(request, 'serverconfig.html',
                      {'username': request.user.userinfo.fullname, "serverconfigpage": True, "id": id,
                       "webaddr": webaddr, "port": port, "usernm": usernm, "passwd": passwd})
    else:
        return HttpResponseRedirect("/login")


def serverconfigsave(request):
    if request.method == 'POST':
        result = ""
        id = request.POST.get('id', '')
        webaddr = request.POST.get('webaddr', '')
        port = request.POST.get('port', '')
        usernm = request.POST.get('usernm', '')
        passwd = request.POST.get('passwd', '')
        cvvendor = Vendor.objects.filter(name='CommVault')
        if (len(cvvendor) > 0):
            cvvendor[
                0].content = "<?xml version=\"1.0\" ?><vendor><webaddr>" + webaddr + "</webaddr><port>" + port + "</port><username>" + usernm + "</username><passwd>" + passwd + "</passwd></vendor>"
            cvvendor[0].save()
            result = "保存成功。"
        else:
            cvvendor = Vendor()
            cvvendor.content = "<?xml version=\"1.0\" ?><vendor><webaddr>" + webaddr + "</webaddr><port>" + port + "</port><username>" + usernm + "</username><passwd>" + passwd + "</passwd></vendor>"
            cvvendor.name = "CommVault"
            cvvendor.save()
            result = "保存成功。"
        return HttpResponse(result)


def match(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        cvvendor = Vendor.objects.filter(name='CommVault')
        id = 0
        webaddr = ""
        port = ""
        usernm = ""
        passwd = ""
        if (len(cvvendor) > 0):
            id = cvvendor[0].id
            doc = parseString(cvvendor[0].content)
            try:
                webaddr = (doc.getElementsByTagName("webaddr"))[0].childNodes[0].data
            except:
                pass
            try:
                port = (doc.getElementsByTagName("port"))[0].childNodes[0].data
            except:
                pass
            try:
                usernm = (doc.getElementsByTagName("username"))[0].childNodes[0].data
            except:
                pass
            try:
                passwd = (doc.getElementsByTagName("passwd"))[0].childNodes[0].data
            except:
                pass
        return render(request, 'match.html',
                      {'username': request.user.userinfo.fullname, "matchpage": True, "id": id, "webaddr": webaddr,
                       "port": port, "usernm": usernm, "passwd": passwd})
    else:
        return HttpResponseRedirect("/login")


def matchdata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                clientName = host.clientName
                platform = host.platform
                agentTypeList = host.agentTypeList
                if host.hostType == "VMWARE":
                    agentTypeList = "<agentTypeList><agentType>Virtual Server</agentType></agentTypeList>"
                installTime = host.installTime.strftime('%Y-%m-%d')
                doc = parseString(agentTypeList)
                agentType = []
                for node in doc.getElementsByTagName("agentTypeList"):
                    for agenttypenode in node.getElementsByTagName("agentType"):
                        agentType.append(agenttypenode.childNodes[0].data)
                result.append({"clientName": clientName, "platform": platform,
                               "agentType": ','.join(agentType), "installTime": installTime})
        return HttpResponse(json.dumps({"data": result}))


def matching(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            result = {}
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            returnclientList = []
            clientList = cvAPI.getClientList()
            for client in clientList:
                allhost = ClientHost.objects.filter(clientID=client["clientId"]).exclude(status="9").filter(
                    Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
                if (len(allhost) > 0):
                    client["selected"] = True
                else:
                    client["selected"] = False
                returnclientList.append(client)
            result = {"value": "1", "list": returnclientList}

            return HttpResponse(json.dumps(result))


def matchsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            result = ""

            password = request.POST.get('password', '')
            clientlist = request.POST.get('clientlist', '')
            myclientlist = clientlist.split("*!-!*")
            myclientlist.remove("")

            oldhost = ClientHost.objects.exclude(status="9").filter(
                Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
            for client in oldhost:
                if str(client.clientID) not in clientlist:
                    client.status = "9"
                    # client.save()
            for listid in myclientlist:
                cvToken = CV_RestApi_Token()
                cvToken.login(info)
                cvAPI = CV_API(cvToken)

                clientInfo = cvAPI.getClientInfo(int(listid))
                newhost = ClientHost.objects.exclude(status="9").filter(
                    Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id)).filter(
                    clientID=int(listid)).exclude(status="9")
                clientName = clientInfo["clientName"]
                hostType = ""
                proxyClient = ""
                creditInfo = ""
                agentTypeList = ""
                platform = clientInfo["platform"]["platform"]
                if "WINDOWS" in (clientInfo["platform"]["platform"]).upper() or "LINUX" in (
                        clientInfo["platform"]["platform"]).upper():
                    hostType = "physical box"
                    agentTypeList = "<agentTypeList>"
                    for node in clientInfo["agentList"]:
                        if node["agentType"] == "File System":
                            agentTypeList += "<agentType>FILESYSTEM</agentType>"
                        else:
                            if node["agentType"] == "Oracle":
                                agentTypeList += "<agentType>ORACLE</agentType>"
                            else:
                                if node["agentType"] == "SQL Server":
                                    agentTypeList += "<agentType>MSSQL</agentType>"
                                else:
                                    agentTypeList += "<agentType>" + node["agentType"] + "</agentType>"
                    agentTypeList += "</agentTypeList>"
                if (clientInfo["platform"]["platform"]).upper() == "ANY":
                    hostType = "VMWARE"
                    creditInfo = "<?xml version=\"1.0\" ?><creditInfo><HOST>" + clientInfo["instance"][
                        "HOST"] + "</HOST><USER>" + clientInfo["instance"]["USER"] + "</USER></creditInfo>"
                    proxyClient = "<?xml version=\"1.0\" ?><PROXYLIST>"
                    for node in clientInfo["instance"]["PROXYLIST"]:
                        proxyhost = ClientHost.objects.exclude(status="9").filter(
                            Q(owernID=request.user.userinfo.userGUID) | Q(
                                userinfo__id=request.user.userinfo.id)).filter(clientID=int(node["clientId"])).exclude(
                            status="9")
                        if len(proxyhost) > 0:
                            proxyClient += "<PROXY>" + proxyhost[0].clientGUID + "</PROXY>"
                        else:
                            clienthost = ClientHost()
                            clienthost.clientGUID = uuid.uuid1()
                            clienthost.clientName = node["clientName"]
                            clienthost.owernID = request.user.userinfo.userGUID
                            clienthost.hostType = "physical box"
                            clienthost.clientID = int(node["clientId"])
                            clienthost.status = "0"
                            clienthost.appGroup = "缺省"
                            clienthost.installTime = datetime.datetime.now()
                            clienthost.save()
                            proxyClient += "<PROXY>" + clienthost.clientGUID + "</PROXY>"
                    proxyClient += "</PROXYLIST>>"
                if len(newhost) > 0:
                    newhost[0].clientName = clientName
                    newhost[0].hostType = hostType
                    newhost[0].proxyClientID = proxyClient
                    newhost[0].creditInfo = creditInfo
                    newhost[0].agentTypeList = agentTypeList
                    newhost[0].platform = platform
                    # newhost[0].save()
                else:
                    newhost = ClientHost()
                    newhost.clientGUID = uuid.uuid1()
                    newhost.owernID = request.user.userinfo.userGUID
                    newhost.clientName = clientName
                    newhost.clientID = int(listid)
                    newhost.hostType = hostType
                    newhost.proxyClientID = proxyClient
                    newhost.creditInfo = creditInfo
                    newhost.agentTypeList = agentTypeList
                    newhost.platform = platform
                    newhost.status = "0"
                    newhost.appGroup = "缺省"
                    newhost.installTime = datetime.datetime.now()
                    # newhost.save()
                for backupset in clientInfo["backupsetList"]:
                    backupInfo = cvAPI.getSubclientInfo(backupset["subclientId"])
                    try:
                        a = 1
                    except:
                        pass

            return HttpResponse(result)


def phyproconfig(request):
    if request.user.is_authenticated():
        backupresource = BackupResource.objects.exclude(state="9")
        fileschduleresource = SchduleResource.objects.exclude(state="9").filter(specifications__contains='type="文件"')
        dbschduleresource = SchduleResource.objects.exclude(state="9").filter(specifications__contains='type="数据库"')
        backups = []
        for backup in backupresource:
            backups.append({"id": backup.id, "name": backup.name + "(" + backup.description + ")"})
        fileschdules = []
        for fileschdule in fileschduleresource:
            fileschdules.append({"id": fileschdule.id, "name": fileschdule.name + "(" + fileschdule.description + ")"})
        dbschdules = []
        for dbschdule in dbschduleresource:
            dbschdules.append({"id": dbschdule.id, "name": dbschdule.name + "(" + dbschdule.description + ")"})
        return render(request, 'phyproconfig.html',
                      {'username': request.user.userinfo.fullname, "backupresource": backups,
                       "fileschduleresource": fileschdules, "dbschduleresource": dbschdules, "phyproconfigpage": True})
    else:
        return HttpResponseRedirect("/login")


def phyproconfigdata(request):
    if request.user.is_authenticated():
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(hostType="physical box").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                id = host.id
                clientName = host.clientName
                clientGUID = host.clientGUID
                platform = host.platform
                agentTypeList = host.agentTypeList
                appGroup = host.appGroup
                status = "否"
                if host.status == "1":
                    status = "是"
                doc = parseString(agentTypeList)
                agentType = []
                for node in doc.getElementsByTagName("agentTypeList"):
                    for agenttypenode in node.getElementsByTagName("agentType"):
                        agentType.append(agenttypenode.childNodes[0].data)
                result.append({"id": id, "clientName": clientName, "clientGUID": clientGUID, "platform": platform,
                               "appGroup": appGroup,
                               "status": status, "agentType": agentType})
        return HttpResponse(json.dumps({"data": result}))


def getphydataget(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = {}
            clientGUID = request.POST.get('clientGUID', '')
            fs = request.POST.get('fs', '')
            oracle = request.POST.get('oracle', '')
            mssql = request.POST.get('mssql', '')

            if fs == "1":
                alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='FILESYSTEM').exclude(status="9")
                if (len(alldataset) > 0):
                    id = alldataset[0].id
                    dataSetGUID = alldataset[0].dataSetGUID
                    content = alldataset[0].content
                    backupContent = ""
                    isBackupOS = ""
                    schdule = ""
                    storage = ""
                    path = []
                    try:
                        doc = parseString(content)
                        try:
                            isBackupOS = (doc.getElementsByTagName("isBackupOS"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            schdule = (doc.getElementsByTagName("schdule"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            storage = (doc.getElementsByTagName("storage"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            backupContent = (doc.getElementsByTagName("backupContent"))[0]
                            for mypath in backupContent.childNodes:
                                try:
                                    path.append(mypath.childNodes[0].data)
                                except:
                                    pass
                        except:
                            pass
                    except:
                        pass
                    result["fs"] = {"id": id, "dataSetGUID": dataSetGUID, "path": path, "isBackupOS": isBackupOS,
                                    "schdule": schdule, "storage": storage}
            if oracle == "1":
                alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='ORACLE').exclude(status="9")
                if (len(alldataset) > 0):
                    id = alldataset[0].id
                    dataSetGUID = alldataset[0].dataSetGUID
                    content = alldataset[0].content
                    name = alldataset[0].instanceName
                    dbschdule = ""
                    logschdule = ""
                    dbstorage = ""
                    logstorage = ""
                    username = ""
                    oraclehome = ""
                    conn1 = ""
                    conn2 = ""
                    conn3 = ""
                    try:
                        doc = parseString(content)
                        try:
                            dbschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            logschdule = (doc.getElementsByTagName("logschdule"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            dbstorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            logstorage = (doc.getElementsByTagName("logstorage"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            backupContentnode = (doc.getElementsByTagName("backupContent"))[0]

                            username = (backupContentnode.getElementsByTagName("username"))[0].childNodes[0].data
                            oraclehome = (backupContentnode.getElementsByTagName("oraclehome"))[0].childNodes[0].data
                            conn1 = (backupContentnode.getElementsByTagName("conn1"))[0].childNodes[0].data
                            conn2 = (backupContentnode.getElementsByTagName("conn2"))[0].childNodes[0].data
                            conn3 = (backupContentnode.getElementsByTagName("conn3"))[0].childNodes[0].data
                        except:
                            pass
                    except:
                        pass
                    result["oracle"] = {"id": id, "dataSetGUID": dataSetGUID, "dbschdule": dbschdule,
                                        "logschdule": logschdule,
                                        "dbstorage": dbstorage, "logstorage": logstorage, "username": username,
                                        "oraclehome": oraclehome, "conn1": conn1, "conn2": conn2, "conn3": conn3,
                                        "name": name}
            if mssql == "1":
                alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='MSSQL').exclude(status="9")
                if (len(alldataset) > 0):
                    id = alldataset[0].id
                    dataSetGUID = alldataset[0].dataSetGUID
                    content = alldataset[0].content
                    name = alldataset[0].instanceName
                    dbschdule = ""
                    logschdule = ""
                    dbstorage = ""
                    logstorage = ""
                    username = ""
                    isvvs = ""
                    iscover = ""
                    try:
                        doc = parseString(content)
                        try:
                            dbschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            logschdule = (doc.getElementsByTagName("logschdule"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            dbstorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            logstorage = (doc.getElementsByTagName("logstorage"))[0].childNodes[0].data
                        except:
                            pass
                        try:
                            backupContentnode = (doc.getElementsByTagName("backupContent"))[0]
                            username = (backupContentnode.getElementsByTagName("username"))[0].childNodes[0].data
                            isvvs = (backupContentnode.getElementsByTagName("isvvs"))[0].childNodes[0].data
                            iscover = (backupContentnode.getElementsByTagName("iscover"))[0].childNodes[0].data
                        except:
                            pass
                    except:
                        pass
                    result["mssql"] = {"id": id, "dataSetGUID": dataSetGUID, "dbschdule": dbschdule,
                                       "logschdule": logschdule,
                                       "dbstorage": dbstorage, "logstorage": logstorage, "username": username,
                                       "isvvs": isvvs, "iscover": iscover, "name": name}
            return HttpResponse(json.dumps(result))


def phyproconfigsaveapp(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = {}
            result["text"] = u"保存成功。"
            clientGUID = request.POST.get('clientGUID', '')
            appGroup = request.POST.get('appGroup', '')

            myclient = ClientHost.objects.get(clientGUID=clientGUID)
            if appGroup == "":
                appGroup = "缺省"
            myclient.appGroup = appGroup
            myclient.save()

            return HttpResponse(json.dumps(result))


def phyproconfigsavefile(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = {}
            result["text"] = u"保存成功。"
            password = request.POST.get('password', '')
            fs = request.POST.get('fs', '')
            clientGUID = request.POST.get('clientGUID', '')
            appGroup = request.POST.get('appGroup', '')
            fs_dataSetGUID = request.POST.get('fs_dataSetGUID', '')
            fs_schdule = request.POST.get('fs_schdule', '')
            fs_storage = request.POST.get('fs_storage', '')
            fs_isBackupOS = request.POST.get('fs_isBackupOS', '')
            fs_backupContent = request.POST.get('fs_backupContent')
            fs_backupContent = fs_backupContent.split("*!-!*")
            fs_isupdate = request.POST.get('fs_isupdate', '')
            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                myclient = ClientHost.objects.get(clientGUID=clientGUID)
                if appGroup == "":
                    appGroup = "缺省"
                myclient.appGroup = appGroup
                myclient.save()

                if (fs == "1"):

                    databaseschdule = ""
                    databasestorage = ""
                    alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='FILESYSTEM').exclude(
                        status="9")
                    if (len(alldataset) > 0):
                        try:
                            databasecontent = alldataset[0].content
                            doc = parseString(databasecontent)
                            try:
                                databaseschdule = (doc.getElementsByTagName("schdule"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                databasestorage = (doc.getElementsByTagName("storage"))[0].childNodes[0].data
                            except:
                                pass
                        except:
                            pass

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'content', None)
                    root = dom.documentElement
                    backupcontentnode = dom.createElement('backupContent')
                    for path in fs_backupContent:
                        if path != "":
                            pathNode = dom.createElement('path')
                            pathTextNode = dom.createTextNode(path)
                            pathNode.appendChild(pathTextNode)
                            backupcontentnode.appendChild(pathNode)
                        else:
                            fs_backupContent.remove(path)

                    if len(fs_backupContent) == 0:
                        pathNode = dom.createElement('path')
                        pathTextNode = dom.createTextNode("\\")
                        pathNode.appendChild(pathTextNode)
                        backupcontentnode.appendChild(pathNode)
                    root.appendChild(backupcontentnode)
                    schduleNode = dom.createElement('schdule')
                    schduleTextNode = dom.createTextNode(fs_schdule)
                    schduleNode.appendChild(schduleTextNode)
                    root.appendChild(schduleNode)
                    storageNode = dom.createElement('storage')
                    storageTextNode = dom.createTextNode(fs_storage)
                    storageNode.appendChild(storageTextNode)
                    root.appendChild(storageNode)
                    isBackupOSNode = dom.createElement('isBackupOS')
                    isBackupOSTextNode = dom.createTextNode(fs_isBackupOS)
                    isBackupOSNode.appendChild(isBackupOSTextNode)
                    root.appendChild(isBackupOSNode)
                    content = dom.toxml()

                    storagename = None
                    schdulename = None
                    if databasestorage != fs_storage or fs_isupdate == 'TRUE':
                        try:
                            storage = BackupResource.objects.get(id=fs_storage)
                            doc = parseString(storage.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    storagename = hostnode.getAttribute("name")
                        except:
                            pass
                    if databaseschdule != fs_schdule or fs_isupdate == 'TRUE':
                        try:
                            schdule = SchduleResource.objects.get(id=fs_schdule)
                            doc = parseString(schdule.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    schdulename = hostnode.getAttribute("name")
                        except:
                            pass

                    paths = fs_backupContent
                    isBackupOS = False
                    if fs_isBackupOS == "TRUE":
                        isBackupOS = True
                    fsBackupContent = {"SPName": storagename, "Schdule": schdulename, "Paths": paths,
                                       "OS": isBackupOS}

                    if fs_dataSetGUID == "0":
                        fs_dataset = DataSet()
                        fs_dataset.dataSetGUID = uuid.uuid1()
                        fs_dataset.clientGUID = myclient.clientGUID
                        fs_dataset.clientName = myclient.clientName
                        fs_dataset.owernID = myclient.owernID
                        fs_dataset.vendor = myclient.vendor
                        fs_dataset.zone = myclient.zone
                        fs_dataset.clientID = myclient.clientID
                        fs_dataset.agentType = "FILESYSTEM"
                        fs_dataset.statu = "0"
                        fs_dataset.content = content
                        fs_dataset.installTime = datetime.datetime.now()
                        fs_dataset.save()
                        result["fs_GUID"] = str(fs_dataset.dataSetGUID)
                    else:
                        fs_dataset = DataSet.objects.get(dataSetGUID=fs_dataSetGUID)
                        fs_dataset.content = content
                        fs_dataset.save()
                        result["fs_GUID"] = str(fs_dataset.dataSetGUID)
                    cvToken = CV_RestApi_Token()
                    cvToken.login(info)
                    cvAPI = CV_API(cvToken)
                    if cvAPI.setFSBackupset(int(myclient.clientID), None, fsBackupContent):
                        pass
                    else:

                        result["text"] += u"应用环境信息异常：服务器端保存失败。" + cvAPI.msg


            else:
                result["text"] = u"密码错误。"

            return HttpResponse(json.dumps(result))


def phyproconfigsaveoracle(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = {}
            result["text"] = u"保存成功。"
            password = request.POST.get('password', '')
            oracle = request.POST.get('oracle', '')
            clientGUID = request.POST.get('clientGUID', '')
            appGroup = request.POST.get('appGroup', '')

            oracle_dataSetGUID = request.POST.get('oracle_dataSetGUID', '')
            oracle_dbschdule = request.POST.get('oracle_dbschdule', '')
            oracle_logschdule = request.POST.get('oracle_logschdule', '')
            oracle_dbstorage = request.POST.get('oracle_dbstorage', '')
            oracle_logstorage = request.POST.get('oracle_logstorage', '')
            oracle_username = request.POST.get('oracle_username', '')
            oracle_name = request.POST.get('oracle_name', '')
            oracle_mypassword = request.POST.get('oracle_mypassword', '')
            oracle_oraclehome = request.POST.get('oracle_oraclehome', '')
            oracle_conn1 = request.POST.get('oracle_conn1', '')
            oracle_conn2 = request.POST.get('oracle_conn2', '')
            oracle_conn3 = request.POST.get('oracle_conn3', '')
            oracle_isupdate = request.POST.get('oracle_isupdate', '')

            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                myclient = ClientHost.objects.get(clientGUID=clientGUID)
                if appGroup == "":
                    appGroup = "缺省"
                myclient.appGroup = appGroup
                myclient.save()

                if (oracle == "1"):
                    databaseschdule = ""
                    databasestorage = ""
                    databaseinstanceName = ""
                    databaseoraclehome = ""
                    databaseusername = ""
                    alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='ORACLE').exclude(status="9")
                    if (len(alldataset) > 0):
                        databaseinstanceName = alldataset[0].instanceName
                        databasecontent = alldataset[0].content
                        try:
                            doc = parseString(databasecontent)
                            try:
                                databaseschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                databasestorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                backupContentnode = (doc.getElementsByTagName("backupContent"))[0]

                                databaseusername = (backupContentnode.getElementsByTagName("username"))[0].childNodes[
                                    0].data
                                databaseoraclehome = \
                                    (backupContentnode.getElementsByTagName("oraclehome"))[0].childNodes[0].data
                            except:
                                pass
                        except:
                            pass

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'content', None)
                    root = dom.documentElement
                    backupNode = dom.createElement('backupContent')
                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username)
                    usernameNode.appendChild(usernameTextNode)
                    backupNode.appendChild(usernameNode)
                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    backupNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1)
                    conn1Node.appendChild(conn1TextNode)
                    backupNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2)
                    conn2Node.appendChild(conn2TextNode)
                    backupNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3)
                    conn3Node.appendChild(conn3TextNode)
                    backupNode.appendChild(conn3Node)
                    root.appendChild(backupNode)

                    schduleNode = dom.createElement('schdule')
                    dbschduleNode = dom.createElement('dbschdule')
                    dbschduleTextNode = dom.createTextNode(oracle_dbschdule)
                    dbschduleNode.appendChild(dbschduleTextNode)
                    schduleNode.appendChild(dbschduleNode)
                    logschduleNode = dom.createElement('logschdule')
                    logschduleTextNode = dom.createTextNode(oracle_logschdule)
                    logschduleNode.appendChild(logschduleTextNode)
                    schduleNode.appendChild(logschduleNode)
                    root.appendChild(schduleNode)
                    storageNode = dom.createElement('storage')
                    dbstorageNode = dom.createElement('dbstorage')
                    dbstorageTextNode = dom.createTextNode(oracle_dbstorage)
                    dbstorageNode.appendChild(dbstorageTextNode)
                    storageNode.appendChild(dbstorageNode)
                    logstorageNode = dom.createElement('logstorage')
                    logstorageTextNode = dom.createTextNode(oracle_logstorage)
                    logstorageNode.appendChild(logstorageTextNode)
                    storageNode.appendChild(logstorageNode)
                    root.appendChild(storageNode)
                    content = dom.toxml()

                    clientName = myclient.clientName
                    clientNames = clientName.split('.')
                    clientName = clientNames[0]
                    storagename = None
                    schdulename = None
                    if databasestorage != oracle_dbstorage or oracle_isupdate == 'TRUE':
                        try:
                            storage = BackupResource.objects.get(id=oracle_dbstorage)
                            doc = parseString(storage.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    storagename = hostnode.getAttribute("name")
                        except:
                            pass
                    if databaseschdule != oracle_dbschdule or oracle_isupdate == 'TRUE':
                        try:
                            schdule = SchduleResource.objects.get(id=oracle_dbschdule)
                            doc = parseString(schdule.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    schdulename = hostnode.getAttribute("name")
                        except:
                            pass
                    oraCreditInfo = None
                    if databaseinstanceName != oracle_name or databasestorage != oracle_dbstorage or databaseoraclehome != oracle_oraclehome or databaseusername != oracle_username or oracle_isupdate == 'TRUE':
                        oraCreditInfo = {"instanceName": oracle_name,
                                         "userName": oracle_username, "passwd": oracle_mypassword, "OCS": "/",
                                         "SPName": storagename,
                                         "ORACLE-HOME": oracle_oraclehome,
                                         "Server": clientName}
                    oraBackupContent = {"SPName": storagename, "Schdule": schdulename}

                    if oracle_dataSetGUID == "0":
                        oracle_dataset = DataSet()
                        oracle_dataset.dataSetGUID = uuid.uuid1()
                        oracle_dataset.clientGUID = myclient.clientGUID
                        oracle_dataset.clientName = myclient.clientName
                        oracle_dataset.owernID = myclient.owernID
                        oracle_dataset.vendor = myclient.vendor
                        oracle_dataset.zone = myclient.zone
                        oracle_dataset.clientID = myclient.clientID
                        oracle_dataset.agentType = "ORACLE"
                        oracle_dataset.statu = "0"
                        oracle_dataset.instanceName = oracle_name
                        oracle_dataset.content = content
                        oracle_dataset.installTime = datetime.datetime.now()
                        oracle_dataset.save()
                        result["oracle_GUID"] = str(oracle_dataset.dataSetGUID)
                    else:
                        oracle_dataset = DataSet.objects.get(dataSetGUID=oracle_dataSetGUID)
                        oracle_dataset.content = content
                        oracle_dataset.instanceName = oracle_name
                        oracle_dataset.save()
                        result["oracle_GUID"] = str(oracle_dataset.dataSetGUID)
                    cvToken = CV_RestApi_Token()
                    cvToken.login(info)
                    cvAPI = CV_API(cvToken)
                    if cvAPI.setOracleBackupset(int(myclient.clientID), oracle_name, oraCreditInfo, oraBackupContent):
                        pass
                    else:
                        # b = cvClient.receiveText
                        # b=b.decode('gbk')
                        result["text"] += u"ORACLE信息异常：服务器端保存失败。" + cvAPI.msg

            else:
                result["text"] = u"密码错误。"

            return HttpResponse(json.dumps(result))


def phyproconfigsavemssql(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = {}
            result["text"] = u"保存成功。"
            password = request.POST.get('password', '')

            mssql = request.POST.get('mssql', '')
            clientGUID = request.POST.get('clientGUID', '')
            appGroup = request.POST.get('appGroup', '')

            mssql_dataSetGUID = request.POST.get('mssql_dataSetGUID', '')
            mssql_dbschdule = request.POST.get('mssql_dbschdule', '')
            mssql_logschdule = request.POST.get('mssql_logschdule', '')
            mssql_dbstorage = request.POST.get('mssql_dbstorage', '')
            mssql_logstorage = request.POST.get('mssql_logstorage', '')
            mssql_name = request.POST.get('mssql_name', '')
            mssql_username = request.POST.get('mssql_username', '')
            mssql_mypassword = request.POST.get('mssql_mypassword', '')
            mssql_isvvs = request.POST.get('mssql_isvvs', '')
            mssql_iscover = request.POST.get('mssql_iscover', '')
            mssql_isupdate = request.POST.get('mssql_isupdate', '')
            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                myclient = ClientHost.objects.get(clientGUID=clientGUID)
                if appGroup == "":
                    appGroup = "缺省"
                myclient.appGroup = appGroup
                myclient.save()
                if (mssql == "1"):
                    databaseschdule = ""
                    databasestorage = ""
                    databaseinstanceName = ""
                    alldataset = DataSet.objects.filter(clientGUID=clientGUID, agentType='MSSQL').exclude(status="9")
                    if (len(alldataset) > 0):
                        databaseinstanceName = alldataset[0].instanceName
                        databasecontent = alldataset[0].content
                        try:
                            doc = parseString(databasecontent)
                            try:
                                databaseschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                databasestorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                            except:
                                pass
                        except:
                            pass

                    impl = xml.dom.minidom.getDOMImplementation()
                    dom = impl.createDocument(None, 'content', None)
                    root = dom.documentElement
                    backupNode = dom.createElement('backupContent')
                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(mssql_username)
                    usernameNode.appendChild(usernameTextNode)
                    backupNode.appendChild(usernameNode)

                    isvvsNode = dom.createElement('isvvs')
                    isvvsTextNode = dom.createTextNode(mssql_isvvs)
                    isvvsNode.appendChild(isvvsTextNode)
                    backupNode.appendChild(isvvsNode)
                    iscoverNode = dom.createElement('iscover')
                    iscoverTextNode = dom.createTextNode(mssql_iscover)
                    iscoverNode.appendChild(iscoverTextNode)
                    backupNode.appendChild(iscoverNode)
                    root.appendChild(backupNode)

                    schduleNode = dom.createElement('schdule')
                    dbschduleNode = dom.createElement('dbschdule')
                    dbschduleTextNode = dom.createTextNode(mssql_dbschdule)
                    dbschduleNode.appendChild(dbschduleTextNode)
                    schduleNode.appendChild(dbschduleNode)
                    logschduleNode = dom.createElement('logschdule')
                    logschduleTextNode = dom.createTextNode(mssql_logschdule)
                    logschduleNode.appendChild(logschduleTextNode)
                    schduleNode.appendChild(logschduleNode)
                    root.appendChild(schduleNode)
                    storageNode = dom.createElement('storage')
                    dbstorageNode = dom.createElement('dbstorage')
                    dbstorageTextNode = dom.createTextNode(mssql_dbstorage)
                    dbstorageNode.appendChild(dbstorageTextNode)
                    storageNode.appendChild(dbstorageNode)
                    logstorageNode = dom.createElement('logstorage')
                    logstorageTextNode = dom.createTextNode(mssql_logstorage)
                    logstorageNode.appendChild(logstorageTextNode)
                    storageNode.appendChild(logstorageNode)
                    root.appendChild(storageNode)
                    content = dom.toxml()

                    clientName = myclient.clientName
                    clientNames = clientName.split('.')
                    clientName = clientNames[0]
                    storagename = None
                    schdulename = None
                    if databasestorage != mssql_dbstorage or mssql_isupdate == 'TRUE':
                        try:
                            storage = BackupResource.objects.get(id=mssql_dbstorage)
                            doc = parseString(storage.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    storagename = hostnode.getAttribute("name")
                        except:
                            pass
                    if databaseschdule != mssql_dbschdule or mssql_isupdate == 'TRUE':
                        try:
                            schdule = SchduleResource.objects.get(id=mssql_dbschdule)
                            doc = parseString(schdule.certificate)
                            for node in doc.getElementsByTagName("CERT_LIST"):
                                for hostnode in node.getElementsByTagName("CERT"):
                                    schdulename = hostnode.getAttribute("name")
                        except:
                            pass
                    mssqlCreditInfo = None
                    if databaseinstanceName != mssql_name or databasestorage != mssql_dbstorage or mssql_isupdate == 'TRUE':
                        mssqlCreditInfo = {"instanceName": mssql_name, "SPName": storagename,
                                           "userName": mssql_username, "passwd": mssql_mypassword,
                                           "useVss": "True", "Server": clientName}
                    mssqlBackupContent = {"SPName": storagename, "Schdule": schdulename}

                    if mssql_dataSetGUID == "0":
                        mssql_dataset = DataSet()
                        mssql_dataset.dataSetGUID = uuid.uuid1()
                        mssql_dataset.clientGUID = myclient.clientGUID
                        mssql_dataset.clientName = myclient.clientName
                        mssql_dataset.owernID = myclient.owernID
                        mssql_dataset.vendor = myclient.vendor
                        mssql_dataset.zone = myclient.zone
                        mssql_dataset.clientID = myclient.clientID
                        mssql_dataset.agentType = "MSSQL"
                        mssql_dataset.instanceName = mssql_name
                        mssql_dataset.statu = "0"
                        mssql_dataset.content = content
                        mssql_dataset.installTime = datetime.datetime.now()
                        mssql_dataset.save()
                        result["mssql_GUID"] = str(mssql_dataset.dataSetGUID)
                    else:
                        mssql_dataset = DataSet.objects.get(dataSetGUID=mssql_dataSetGUID)
                        mssql_dataset.content = content
                        mssql_dataset.instanceName = mssql_name
                        mssql_dataset.save()
                        result["mssql_GUID"] = str(mssql_dataset.dataSetGUID)
                    cvToken = CV_RestApi_Token()
                    cvToken.login(info)
                    cvAPI = CV_API(cvToken)
                    if cvAPI.setMssqlBackupset(int(myclient.clientID), mssql_name, mssqlCreditInfo, mssqlBackupContent):
                        pass
                    else:
                        # b = cvClient.receiveText
                        # b=b.decode('gbk')
                        result["text"] += u"MSSQL信息异常：服务器端保存失败。" + cvAPI.msg

            else:
                result["text"] = u"密码错误。"

            return HttpResponse(json.dumps(result))


def vmproconfig(request):
    if request.user.is_authenticated():
        backupresource = BackupResource.objects.exclude(state="9")
        schduleresource = SchduleResource.objects.exclude(state="9").filter(specifications__contains='type="虚机"')
        backups = []
        for backup in backupresource:
            backups.append({"id": backup.id, "name": backup.name + "(" + backup.description + ")"})
        schdules = []
        for schdule in schduleresource:
            schdules.append({"id": schdule.id, "name": schdule.name + "(" + schdule.description + ")"})

        allhost = ClientHost.objects.exclude(status="9").filter(hostType="physical box").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        pyhhost = []
        if (len(allhost) > 0):
            for host in allhost:
                agentTypeList = host.agentTypeList
                doc = parseString(agentTypeList)
                for node in doc.getElementsByTagName("agentTypeList"):
                    for agenttypenode in node.getElementsByTagName("agentType"):
                        if agenttypenode.childNodes[0].data == "Virtual Server":
                            clientName = host.clientName
                            pyhhost.append({"GUID": host.clientGUID, "NAME": clientName})
                            break
        return render(request, 'vmproconfig.html',
                      {'username': request.user.userinfo.fullname, "backupresource": backups,
                       "schduleresource": schdules, "pyhhost": pyhhost, "vmproconfigpage": True})
    else:
        return HttpResponseRedirect("/login")


def vmproconfigdata(request):
    if request.user.is_authenticated():
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(hostType="VMWARE").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                clientName = host.clientName
                clientGUID = host.clientGUID
                proxyClientID = host.proxyClientID
                creditInfo = host.creditInfo
                platform = host.platform
                status = "否"
                if host.status == "1":
                    status = "是"
                proxylist = []

                hostname = ""
                username = ""
                password = ""
                if creditInfo != "" and creditInfo != None:
                    doc = parseString(creditInfo)
                    for node in doc.getElementsByTagName("creditInfo"):
                        for hostnode in node.getElementsByTagName("HOST"):
                            hostname = hostnode.childNodes[0].data
                        for usernode in node.getElementsByTagName("USER"):
                            username = usernode.childNodes[0].data
                        for passwordnode in node.getElementsByTagName("PASSWD"):
                            password = passwordnode.childNodes[0].data
                if proxyClientID != "" and proxyClientID != None:
                    doc = parseString(proxyClientID)
                    for node in doc.getElementsByTagName("PROXYLIST"):
                        for proxylistnode in node.getElementsByTagName("PROXY"):
                            try:
                                proxy = ClientHost.objects.get(clientGUID=proxylistnode.childNodes[0].data)
                                proxylist.append({"clientGUID": proxy.clientGUID, "clientName": proxy.clientName, })
                            except:
                                pass

                alldataset = DataSet.objects.filter(clientGUID=clientGUID).exclude(status="9")
                if len(alldataset) > 0:
                    for dataset in alldataset:
                        appGroup = dataset.appGroup
                        dataSetGUID = dataset.dataSetGUID
                        content = dataset.content
                        schdule = ""
                        storage = ""
                        backupContentlist = []
                        if content != "" and content != None:
                            doc = parseString(content)
                            try:
                                schdule = (doc.getElementsByTagName("schdule"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                storage = (doc.getElementsByTagName("storage"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                for node in doc.getElementsByTagName("backupContent"):
                                    a = len(node.getElementsByTagName("VM"))
                                    for vmlistnode in node.getElementsByTagName("VM"):
                                        try:
                                            backupContentlist.append(vmlistnode.childNodes[0].data)

                                        except:
                                            pass
                            except:
                                pass

                        result.append(
                            {"clientName": clientName, "clientGUID": clientGUID, "platform": platform,
                             "proxylist": proxylist, "hostname": hostname, "username": username, "password": password,
                             "appGroup": appGroup,
                             "status": status, "dataSetGUID": dataSetGUID, "schdule": schdule, "storage": storage,
                             "backupContent": backupContentlist})
                else:
                    result.append(
                        {"clientName": clientName, "clientGUID": clientGUID, "platform": platform,
                         "proxylist": proxylist, "hostname": hostname, "username": username, "password": password,
                         "appGroup": "",
                         "status": status, "dataSetGUID": "", "schdule": "", "storage": "", "backupContent": []})
        return HttpResponse(json.dumps({"data": result}))


def getvmlist(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        if request.method == 'POST':
            result = []
            clientGUID = request.POST.get('clientGUID', '')
            allhost = ClientHost.objects.exclude(status="9").filter(hostType="VMWARE").filter(
                clientGUID=clientGUID)
            if (len(allhost) > 0):
                cvToken = CV_RestApi_Token()
                cvToken.login(info)
                cvAPI = CV_API(cvToken)
                vmlist = cvAPI.getVMWareVMList(allhost[0].clientName)
                for node in vmlist:
                    result.append({"vmid": node["VMName"], "vmname": node["VMName"]})

        return HttpResponse(json.dumps(result))


def vmproconfigsave(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = ""

            password = request.POST.get('password', '')
            clientGUID = request.POST.get('clientGUID', '')
            clientName = request.POST.get('clientName', '')
            hostname = request.POST.get('hostname', '')
            username = request.POST.get('username', '')
            mypassword = request.POST.get('mypassword', '')
            pyhhostlist = request.POST.get('pyhhostlist', '')
            pyhhostlist = pyhhostlist.split("*!-!*")

            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                creditInfo = ""
                proxyClientID = ""

                impl = xml.dom.minidom.getDOMImplementation()
                dom = impl.createDocument(None, 'creditInfo', None)
                root = dom.documentElement
                hostnamenode = dom.createElement('HOST')
                hostnameTextNode = dom.createTextNode(hostname)
                hostnamenode.appendChild(hostnameTextNode)
                root.appendChild(hostnamenode)
                usernamenode = dom.createElement('USER')
                usernameTextNode = dom.createTextNode(username)
                usernamenode.appendChild(usernameTextNode)
                root.appendChild(usernamenode)
                # passwordnode = dom.createElement('PASSWD')
                # passwordTextNode = dom.createTextNode(mypassword)
                # passwordnode.appendChild(passwordTextNode)
                # root.appendChild(passwordnode)
                creditInfo = dom.toxml()

                root = dom.documentElement
                dom = impl.createDocument(None, 'PROXYLIST', None)
                root = dom.documentElement
                for pyhhost in pyhhostlist:
                    if pyhhost != "":
                        proxyNode = dom.createElement('PROXY')
                        proxyTextNode = dom.createTextNode(pyhhost)
                        proxyNode.appendChild(proxyTextNode)
                        root.appendChild(proxyNode)
                proxyClientID = dom.toxml()

                if clientGUID == "0":
                    vsProxy = []
                    for pyhhost in pyhhostlist:
                        if pyhhost != "":
                            try:
                                pyclient = ClientHost.objects.get(clientGUID=pyhhost)
                                vsProxy.append(pyclient.clientName)
                            except:
                                pass
                    if len(vsProxy) == 0:
                        vsProxy = [""]
                    vsaClientInfo = {"vCenterHost": hostname, "proxyList": vsProxy, "userName": username,
                                     "passwd": mypassword}

                    cvToken = CV_RestApi_Token()
                    cvToken.login(info)
                    cvAPI = CV_API(cvToken)
                    rc = cvAPI.setVMWareClient(clientName + "." + request.user.username, vsaClientInfo)
                    if rc:
                        clientID = 0
                        try:
                            clentinfo = cvAPI.getClientInfo(clientName + "." + request.user.username)
                            clientID = clentinfo["clientId"]
                        except:
                            pass
                        client = ClientHost()
                        client.clientGUID = uuid.uuid1()
                        client.clientName = clientName + "." + request.user.username
                        client.owernID = request.user.userinfo.userGUID
                        client.clientID = clientID
                        client.hostType = "VMWARE"
                        client.proxyClientID = proxyClientID
                        client.creditInfo = creditInfo
                        client.status = "0"
                        client.platform = "VMWARE"
                        client.installTime = datetime.datetime.now()
                        client.save()
                        result = u"保存成功。"
                    else:
                        # b = cvClient.receiveText
                        # b=b.decode('gbk')
                        result = u"服务器端异常:" + cvAPI.msg + u",新增失败。"
                else:
                    client = ClientHost.objects.get(clientGUID=clientGUID)
                    client.creditInfo = creditInfo
                    client.proxyClientID = proxyClientID
                    client.clientName = clientName + "." + request.user.username
                    client.save()
                    result = u"保存成功。"

            else:
                result = u"密码错误。"

            return HttpResponse(result)


def vmappsave(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = ""

            password = request.POST.get('password', '')
            dataSetGUID = request.POST.get('dataSetGUID', '')
            appGroup = request.POST.get('appGroup', '')
            backupContent = request.POST.get('backupContent', '')
            schdule = request.POST.get('schdule', '')
            storage = request.POST.get('storage', '')
            myclientGUID = request.POST.get('myclientGUID', '')
            backupContentlist = backupContent.split("*!-!*")
            backupContentlist.remove("")

            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                content = ""
                impl = xml.dom.minidom.getDOMImplementation()
                dom = impl.createDocument(None, 'content', None)
                root = dom.documentElement
                backupcontentnode = dom.createElement('backupContent')
                for backupContent in backupContentlist:
                    if backupContent != "":
                        vmNode = dom.createElement('VM')
                        vmTextNode = dom.createTextNode(backupContent)
                        vmNode.appendChild(vmTextNode)
                        backupcontentnode.appendChild(vmNode)
                root.appendChild(backupcontentnode)
                schduleNode = dom.createElement('schdule')
                schduleTextNode = dom.createTextNode(schdule)
                schduleNode.appendChild(schduleTextNode)
                root.appendChild(schduleNode)
                storageNode = dom.createElement('storage')
                storageTextNode = dom.createTextNode(storage)
                storageNode.appendChild(storageTextNode)
                root.appendChild(storageNode)
                content = dom.toxml()
                myclient = ClientHost.objects.get(clientGUID=myclientGUID)

                databaseschdule = ""
                databasestorage = ""
                alldataset = DataSet.objects.filter(dataSetGUID=dataSetGUID)
                if (len(alldataset) > 0):
                    databasecontent = alldataset[0].content
                    doc = parseString(databasecontent)
                    try:
                        databaseschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                    except:
                        pass
                    try:
                        databasestorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                    except:
                        pass
                storagename = None
                schdulename = None
                if databasestorage != storage:
                    try:
                        storage = BackupResource.objects.get(id=storage)
                        doc = parseString(storage.certificate)
                        for node in doc.getElementsByTagName("CERT_LIST"):
                            for hostnode in node.getElementsByTagName("CERT"):
                                storagename = hostnode.getAttribute("name")
                    except:
                        pass
                if databaseschdule != schdule:
                    try:
                        schdule = SchduleResource.objects.get(id=schdule)
                        doc = parseString(schdule.certificate)
                        for node in doc.getElementsByTagName("CERT_LIST"):
                            for hostnode in node.getElementsByTagName("CERT"):
                                schdulename = hostnode.getAttribute("name")
                    except:
                        pass

                if dataSetGUID == "0":
                    dataset = DataSet()
                    dataset.dataSetGUID = uuid.uuid1()
                    dataset.clientGUID = myclient.clientGUID
                    dataset.clientName = myclient.clientName
                    dataset.owernID = myclient.owernID
                    dataset.vendor = myclient.vendor
                    dataset.zone = myclient.zone
                    dataset.clientID = myclient.clientID
                    dataset.agentType = "Virtual Server"
                    dataset.statu = "0"
                    dataset.content = content
                    dataset.installTime = datetime.datetime.now()
                    dataset.appGroup = appGroup
                    dataset.save()
                    result = "保存成功。"
                else:
                    dataset = DataSet.objects.get(dataSetGUID=dataSetGUID)
                    dataset.content = content
                    dataset.appGroup = appGroup
                    dataset.save()
                    result = "保存成功。"

                proxylist = []
                if myclient.proxyClientID != "" and myclient.proxyClientID != None:
                    doc = parseString(myclient.proxyClientID)
                    for node in doc.getElementsByTagName("PROXYLIST"):
                        for proxylistnode in node.getElementsByTagName("PROXY"):
                            try:
                                proxy = ClientHost.objects.get(clientGUID=proxylistnode.childNodes[0].data)
                                listclientName = proxy.clientName
                                proxylist.append(listclientName)
                            except:
                                pass

                vsaBackupsetInfo = {"proxyList": proxylist, "vmList": backupContentlist, "SPName": storagename,
                                    "Schdule": schdulename}
                cvToken = CV_RestApi_Token()
                cvToken.login(info)
                cvAPI = CV_API(cvToken)
                if cvAPI.setVMWareBackupset(myclient.clientName, appGroup, vsaBackupsetInfo):
                    pass
                else:
                    result += u"虚机信息异常：服务器端保存失败。" + cvAPI.msg

            else:
                result = u"密码错误。"

            return HttpResponse(result)


def vmproconfigdel(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            clientGUID = request.POST.get('clientGUID', '')
            client = ClientHost.objects.get(clientGUID=clientGUID)
            info = {"webaddr": "test1", "port": "81", "username": "cvadmin", "passwd": "1qaz@WSX", "token": "",
                    "lastlogin": 0}
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvClient = CV_Client(cvToken, None)
            rs = cvClient.delVSAClient(client.clientName)
            if rs:
                client.status = "9"
                client.save()
                return HttpResponse("删除成功。")
            else:
                return HttpResponse(u"服务器端异常:" + cvClient.msg + u"，删除失败。")
        else:
            return HttpResponse("删除失败。")


def vmappdel(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            dataSetGUID = request.POST.get('dataSetGUID', '')
            dataset = DataSet.objects.get(dataSetGUID=dataSetGUID)
            dataset.status = "9"
            dataset.save()
            return HttpResponse("删除成功。")
        else:
            return HttpResponse("删除失败。")


def racproconfig(request):
    if request.user.is_authenticated():
        backupresource = BackupResource.objects.exclude(state="9")
        schduleresource = SchduleResource.objects.exclude(state="9").filter(specifications__contains='type="数据库"')
        backups = []
        for backup in backupresource:
            backups.append({"id": backup.id, "name": backup.name + "(" + backup.description + ")"})
        schdules = []
        for schdule in schduleresource:
            schdules.append({"id": schdule.id, "name": schdule.name + "(" + schdule.description + ")"})

        allhost = ClientHost.objects.exclude(status="9").filter(hostType="physical box").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        pyhhost = []
        if (len(allhost) > 0):
            for host in allhost:
                agentTypeList = host.agentTypeList
                doc = parseString(agentTypeList)
                for node in doc.getElementsByTagName("agentTypeList"):
                    for agenttypenode in node.getElementsByTagName("agentType"):
                        if agenttypenode.childNodes[0].data == "ORACLE":
                            clientName = host.clientName
                            pyhhost.append({"GUID": host.clientGUID, "NAME": clientName})
                            break
        return render(request, 'racproconfig.html',
                      {'username': request.user.userinfo.fullname, "backupresource": backups,
                       "schduleresource": schdules, "pyhhost": pyhhost, "racproconfigpage": True})
    else:
        return HttpResponseRedirect("/login")


def racproconfigdata(request):
    if request.user.is_authenticated():
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(hostType="RAC").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                clientName = host.clientName
                clientGUID = host.clientGUID
                platform = host.platform
                proxyClientID = host.proxyClientID
                status = "否"
                if host.status == "1":
                    status = "是"
                proxylist = []
                if proxyClientID != "" and proxyClientID != None:
                    doc = parseString(proxyClientID)
                    for node in doc.getElementsByTagName("PROXYLIST"):
                        for proxylistnode in node.getElementsByTagName("PROXY"):
                            try:
                                proxy = ClientHost.objects.get(clientGUID=proxylistnode.childNodes[0].data)
                                listclientName = proxy.clientName
                                proxylist.append({"clientGUID": proxy.clientGUID, "clientName": listclientName})
                            except:
                                pass
                oracle_dbschdule = ""
                oracle_logschdule = ""
                oracle_dbstorage = ""
                oracle_logstorage = ""
                raclist = []
                databaseName = ""
                dataSetGUID = ""

                dataset = DataSet.objects.exclude(status="9").filter(clientGUID=clientGUID)
                if (len(dataset) > 0):
                    dataSetGUID = dataset[0].dataSetGUID
                    databaseName = dataset[0].instanceName
                    content = dataset[0].content
                    doc = parseString(content)
                    try:
                        oracle_dbschdule = (doc.getElementsByTagName("dbschdule"))[0].childNodes[0].data
                    except:
                        pass
                    try:
                        oracle_logschdule = (doc.getElementsByTagName("logschdule"))[0].childNodes[0].data
                    except:
                        pass
                    try:
                        oracle_dbstorage = (doc.getElementsByTagName("dbstorage"))[0].childNodes[0].data
                    except:
                        pass
                    try:
                        oracle_logstorage = (doc.getElementsByTagName("logstorage"))[0].childNodes[0].data
                    except:
                        pass
                    try:
                        backupContentnode = (doc.getElementsByTagName("backupContent"))[0]
                        for raclistnode in backupContentnode.getElementsByTagName("rac"):
                            rac_name = ""
                            rac_username = ""
                            rac_oraclehome = ""
                            rac_conn1 = ""
                            rac_conn2 = ""
                            rac_conn3 = ""
                            pyhGUID = ""
                            pyhclientName = ""
                            try:
                                pyhGUID = (raclistnode.getElementsByTagName("pyhGUID"))[0].childNodes[0].data
                                pyhclient = ClientHost.objects.exclude(status="9").filter(clientGUID=pyhGUID)
                                if len(pyhclient) > 0:
                                    pyhclientName = pyhclient[0].clientName
                            except:
                                pass

                            try:
                                rac_name = (raclistnode.getElementsByTagName("name"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                rac_username = (raclistnode.getElementsByTagName("username"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                rac_oraclehome = (raclistnode.getElementsByTagName("oraclehome"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                rac_conn1 = (raclistnode.getElementsByTagName("conn1"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                rac_conn2 = (raclistnode.getElementsByTagName("conn2"))[0].childNodes[0].data
                            except:
                                pass
                            try:
                                rac_conn3 = (raclistnode.getElementsByTagName("conn3"))[0].childNodes[0].data
                            except:
                                pass
                            raclist.append({"pyhGUID": pyhGUID, "pyhclientName": pyhclientName, "name": rac_name,
                                            "username": rac_username, "oraclehome": rac_oraclehome,
                                            "conn1": rac_conn1, "conn2": rac_conn2, "conn3": rac_conn3})
                    except:
                        pass

                result.append({"clientName": clientName, "clientGUID": clientGUID, "platform": platform,
                               "dataSetGUID": dataSetGUID, "proxylist": proxylist,
                               "status": status, "databaseName": databaseName, "oracle_dbschdule": oracle_dbschdule,
                               "oracle_logschdule": oracle_logschdule
                                  , "oracle_dbstorage": oracle_dbstorage, "oracle_logstorage": oracle_logstorage,
                               "raclist": raclist})
        return HttpResponse(json.dumps({"data": result}))


def racproconfigsave(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = u"保存成功。"
            password = request.POST.get('password', '')
            clientGUID = request.POST.get('clientGUID', '')
            clientName = request.POST.get('clientName', '')
            databaseName = request.POST.get('databaseName', '')
            dataSetGUID = request.POST.get('dataSetGUID', '')
            pyhhostlist = request.POST.get('pyhhostlist', '')
            pyhhostlist = pyhhostlist.split("*!-!*")
            oracle_dbschdule = request.POST.get('oracle_dbschdule', '')
            oracle_logschdule = request.POST.get('oracle_logschdule', '')
            oracle_dbstorage = request.POST.get('oracle_dbstorage', '')
            oracle_logstorage = request.POST.get('oracle_logstorage', '')

            oracle_name_1 = request.POST.get('oracle_name_1', '')
            oracle_username_1 = request.POST.get('oracle_username_1', '')
            oracle_mypassword_1 = request.POST.get('oracle_mypassword_1', '')
            oracle_oraclehome_1 = request.POST.get('oracle_oraclehome_1', '')
            oracle_conn1_1 = request.POST.get('oracle_conn1_1', '')
            oracle_conn2_1 = request.POST.get('oracle_conn2_1', '')
            oracle_conn3_1 = request.POST.get('oracle_conn3_1', '')
            oracle_pyhGUID_1 = request.POST.get('oracle_pyhGUID_1', '')

            oracle_name_2 = request.POST.get('oracle_name_2', '')
            oracle_username_2 = request.POST.get('oracle_username_2', '')
            oracle_mypassword_2 = request.POST.get('oracle_mypassword_2', '')
            oracle_oraclehome_2 = request.POST.get('oracle_oraclehome_2', '')
            oracle_conn1_2 = request.POST.get('oracle_conn1_2', '')
            oracle_conn2_2 = request.POST.get('oracle_conn2_2', '')
            oracle_conn3_2 = request.POST.get('oracle_conn3_2', '')
            oracle_pyhGUID_2 = request.POST.get('oracle_pyhGUID_2', '')

            oracle_name_3 = request.POST.get('oracle_name_3', '')
            oracle_username_3 = request.POST.get('oracle_username_3', '')
            oracle_mypassword_3 = request.POST.get('oracle_mypassword_3', '')
            oracle_oraclehome_3 = request.POST.get('oracle_oraclehome_3', '')
            oracle_conn1_3 = request.POST.get('oracle_conn1_3', '')
            oracle_conn2_3 = request.POST.get('oracle_conn2_3', '')
            oracle_conn3_3 = request.POST.get('oracle_conn3_3', '')
            oracle_pyhGUID_3 = request.POST.get('oracle_pyhGUID_3', '')

            oracle_name_4 = request.POST.get('oracle_name_4', '')
            oracle_username_4 = request.POST.get('oracle_username_4', '')
            oracle_mypassword_4 = request.POST.get('oracle_mypassword_4', '')
            oracle_oraclehome_4 = request.POST.get('oracle_oraclehome_4', '')
            oracle_conn1_4 = request.POST.get('oracle_conn1_4', '')
            oracle_conn2_4 = request.POST.get('oracle_conn2_4', '')
            oracle_conn3_4 = request.POST.get('oracle_conn3_4', '')
            oracle_pyhGUID_4 = request.POST.get('oracle_pyhGUID_4', '')

            oracle_name_5 = request.POST.get('oracle_name_5', '')
            oracle_username_5 = request.POST.get('oracle_username_5', '')
            oracle_mypassword_5 = request.POST.get('oracle_mypassword_5', '')
            oracle_oraclehome_5 = request.POST.get('oracle_oraclehome_5', '')
            oracle_conn1_5 = request.POST.get('oracle_conn1_5', '')
            oracle_conn2_5 = request.POST.get('oracle_conn2_5', '')
            oracle_conn3_5 = request.POST.get('oracle_conn3_5', '')
            oracle_pyhGUID_5 = request.POST.get('oracle_pyhGUID_5', '')

            user = auth.authenticate(username=request.user.username, password=password)
            if user is not None and user.is_active:
                proxyClientID = ""
                impl = xml.dom.minidom.getDOMImplementation()
                dom = impl.createDocument(None, 'PROXYLIST', None)
                root = dom.documentElement
                for pyhhost in pyhhostlist:
                    if pyhhost != "":
                        proxyNode = dom.createElement('PROXY')
                        proxyTextNode = dom.createTextNode(pyhhost)
                        proxyNode.appendChild(proxyTextNode)
                        root.appendChild(proxyNode)
                proxyClientID = dom.toxml()

                content = ""
                impl = xml.dom.minidom.getDOMImplementation()
                dom = impl.createDocument(None, 'content', None)
                root = dom.documentElement
                dbschduleNode = dom.createElement('dbschdule')
                dbschduleTextNode = dom.createTextNode(oracle_dbschdule)
                dbschduleNode.appendChild(dbschduleTextNode)
                root.appendChild(dbschduleNode)
                logschduleNode = dom.createElement('logschdule')
                logschduleTextNode = dom.createTextNode(oracle_logschdule)
                logschduleNode.appendChild(logschduleTextNode)
                root.appendChild(logschduleNode)
                dbstorageNode = dom.createElement('dbstorage')
                dbstorageTextNode = dom.createTextNode(oracle_dbstorage)
                dbstorageNode.appendChild(dbstorageTextNode)
                root.appendChild(dbstorageNode)
                logstorageNode = dom.createElement('logstorage')
                logstorageTextNode = dom.createTextNode(oracle_logstorage)
                logstorageNode.appendChild(logstorageTextNode)
                root.appendChild(logstorageNode)
                backupNode = dom.createElement('backupContent')
                if (oracle_pyhGUID_1 != "0"):
                    racNode = dom.createElement('rac')

                    pyhNode = dom.createElement('pyhGUID')
                    pyhTextNode = dom.createTextNode(oracle_pyhGUID_1)

                    pyhNode.appendChild(pyhTextNode)
                    racNode.appendChild(pyhNode)

                    nameNode = dom.createElement('name')
                    nameTextNode = dom.createTextNode(oracle_name_1)
                    nameNode.appendChild(nameTextNode)
                    racNode.appendChild(nameNode)

                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username_1)
                    usernameNode.appendChild(usernameTextNode)
                    racNode.appendChild(usernameNode)

                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome_1)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    racNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1_1)
                    conn1Node.appendChild(conn1TextNode)
                    racNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2_1)
                    conn2Node.appendChild(conn2TextNode)
                    racNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3_1)
                    conn3Node.appendChild(conn3TextNode)
                    racNode.appendChild(conn3Node)
                    backupNode.appendChild(racNode)
                if (oracle_pyhGUID_2 != "0"):
                    racNode = dom.createElement('rac')
                    pyhNode = dom.createElement('pyhGUID')
                    pyhTextNode = dom.createTextNode(oracle_pyhGUID_2)
                    pyhNode.appendChild(pyhTextNode)
                    racNode.appendChild(pyhNode)
                    nameNode = dom.createElement('name')
                    nameTextNode = dom.createTextNode(oracle_name_2)
                    nameNode.appendChild(nameTextNode)
                    racNode.appendChild(nameNode)

                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username_2)
                    usernameNode.appendChild(usernameTextNode)
                    racNode.appendChild(usernameNode)

                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome_2)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    racNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1_2)
                    conn1Node.appendChild(conn1TextNode)
                    racNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2_2)
                    conn2Node.appendChild(conn2TextNode)
                    racNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3_2)
                    conn3Node.appendChild(conn3TextNode)
                    racNode.appendChild(conn3Node)
                    backupNode.appendChild(racNode)
                if (oracle_pyhGUID_3 != "0"):
                    racNode = dom.createElement('rac')
                    pyhNode = dom.createElement('pyhGUID')
                    pyhTextNode = dom.createTextNode(oracle_pyhGUID_3)
                    pyhNode.appendChild(pyhTextNode)
                    racNode.appendChild(pyhNode)
                    nameNode = dom.createElement('name')
                    nameTextNode = dom.createTextNode(oracle_name_3)
                    nameNode.appendChild(nameTextNode)
                    racNode.appendChild(nameNode)

                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username_3)
                    usernameNode.appendChild(usernameTextNode)
                    racNode.appendChild(usernameNode)

                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome_3)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    racNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1_3)
                    conn1Node.appendChild(conn1TextNode)
                    racNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2_3)
                    conn2Node.appendChild(conn2TextNode)
                    racNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3_3)
                    conn3Node.appendChild(conn3TextNode)
                    racNode.appendChild(conn3Node)
                    backupNode.appendChild(racNode)
                if (oracle_pyhGUID_4 != "0"):
                    racNode = dom.createElement('rac')
                    pyhNode = dom.createElement('pyhGUID')
                    pyhTextNode = dom.createTextNode(oracle_pyhGUID_4)
                    pyhNode.appendChild(pyhTextNode)
                    racNode.appendChild(pyhNode)
                    nameNode = dom.createElement('name')
                    nameTextNode = dom.createTextNode(oracle_name_4)
                    nameNode.appendChild(nameTextNode)
                    racNode.appendChild(nameNode)

                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username_4)
                    usernameNode.appendChild(usernameTextNode)
                    racNode.appendChild(usernameNode)

                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome_4)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    racNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1_4)
                    conn1Node.appendChild(conn1TextNode)
                    racNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2_4)
                    conn2Node.appendChild(conn2TextNode)
                    racNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3_4)
                    conn3Node.appendChild(conn3TextNode)
                    racNode.appendChild(conn3Node)
                    backupNode.appendChild(racNode)
                if (oracle_pyhGUID_5 != "0"):
                    racNode = dom.createElement('rac')
                    pyhNode = dom.createElement('pyhGUID')
                    pyhTextNode = dom.createTextNode(oracle_pyhGUID_5)
                    pyhNode.appendChild(pyhTextNode)
                    racNode.appendChild(pyhNode)
                    nameNode = dom.createElement('name')
                    nameTextNode = dom.createTextNode(oracle_name_5)
                    nameNode.appendChild(nameTextNode)
                    racNode.appendChild(nameNode)

                    usernameNode = dom.createElement('username')
                    usernameTextNode = dom.createTextNode(oracle_username_5)
                    usernameNode.appendChild(usernameTextNode)
                    racNode.appendChild(usernameNode)

                    oraclehomeNode = dom.createElement('oraclehome')
                    oraclehomeTextNode = dom.createTextNode(oracle_oraclehome_5)
                    oraclehomeNode.appendChild(oraclehomeTextNode)
                    racNode.appendChild(oraclehomeNode)
                    conn1Node = dom.createElement('conn1')
                    conn1TextNode = dom.createTextNode(oracle_conn1_5)
                    conn1Node.appendChild(conn1TextNode)
                    racNode.appendChild(conn1Node)
                    conn2Node = dom.createElement('conn2')
                    conn2TextNode = dom.createTextNode(oracle_conn2_5)
                    conn2Node.appendChild(conn2TextNode)
                    racNode.appendChild(conn2Node)
                    conn3Node = dom.createElement('conn3')
                    conn3TextNode = dom.createTextNode(oracle_conn3_5)
                    conn3Node.appendChild(conn3TextNode)
                    racNode.appendChild(conn3Node)
                    backupNode.appendChild(racNode)
                root.appendChild(backupNode)
                content = dom.toxml()

                if clientGUID == "0":
                    client = ClientHost()
                    client.clientGUID = uuid.uuid1()
                    client.clientName = clientName + "." + request.user.username
                    client.owernID = request.user.userinfo.userGUID
                    client.hostType = "RAC"
                    client.proxyClientID = proxyClientID
                    client.status = "0"
                    client.platform = "RAC"
                    client.installTime = datetime.datetime.now()
                    client.save()

                    dataset = DataSet()
                    dataset.dataSetGUID = uuid.uuid1()
                    dataset.clientGUID = client.clientGUID
                    dataset.clientName = client.clientName
                    dataset.owernID = client.owernID
                    dataset.vendor = client.vendor
                    dataset.zone = client.zone
                    dataset.clientID = client.clientID
                    dataset.agentType = "RAC"
                    dataset.statu = "0"
                    dataset.instanceName = databaseName
                    dataset.content = content
                    dataset.installTime = datetime.datetime.now()
                    dataset.save()
                else:
                    client = ClientHost.objects.get(clientGUID=clientGUID)
                    client.proxyClientID = proxyClientID
                    client.clientName = clientName + "." + request.user.username
                    client.save()

                    dataset = DataSet.objects.get(dataSetGUID=dataSetGUID)
                    dataset.content = content
                    dataset.instanceName = databaseName
                    dataset.save()
            else:
                result = u"密码错误。"

            return HttpResponse(result)


def racproconfigdel(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            clientGUID = request.POST.get('clientGUID', '')
            dataSetGUID = request.POST.get('dataSetGUID', '')
            client = ClientHost.objects.get(clientGUID=clientGUID)
            client.status = "9"
            client.save()

            dataset = DataSet.objects.get(dataSetGUID=dataSetGUID)
            dataset.status = "9"
            dataset.save()
            return HttpResponse("删除成功。")
        else:
            return HttpResponse("删除失败。")


def workflowset(request):
    if request.user.is_authenticated():
        processes = Process.objects.exclude(state="9").order_by("sort")
        processlist = []
        for process in processes:
            processlist.append({"id": process.id, "code": process.code, "name": process.name})
        grouplist = []
        allgroup = Group.objects.all().exclude(state="9")
        for group in allgroup:
            grouplist.append({"id": group.id, "name": group.name})
        return render(request, 'workflowset.html',
                      {'username': request.user.userinfo.fullname, "grouplist": grouplist, "processlist": processlist,
                       "workflowsetpage": True})
    else:
        return HttpResponseRedirect("/login")


def getsetps(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = []
            process = request.POST.get('process', '')
            try:
                process = int(process)
            except:
                raise Http404()
            processes = Process.objects.exclude(state="9").filter(id=process)
            if len(processes) > 0:
                pnode_steplist = Step.objects.exclude(state="9").filter(process=processes[0]).order_by("sort").filter(
                    pnode_id=None)
                for pstep in pnode_steplist:
                    p_id = pstep.id
                    curstring = ""
                    if pstep.approval == "1":
                        curstring += "需审批"
                    if pstep.skip == "1":
                        curstring += "可跳过"
                    result.append({"id": pstep.id, "code": pstep.code, "name": pstep.name, "approval": pstep.approval,
                                   "skip": pstep.skip, "group": pstep.group, "time": pstep.time,
                                   "curstring": curstring})
                    inner_steps = Step.objects.exclude(state="9").filter(process=processes[0]).order_by("sort").filter(
                        pnode_id=p_id)
                    for step in inner_steps:
                        curstring = ""
                        if step.approval == "1":
                            curstring += "需审批"
                        if step.skip == "1":
                            curstring += "可跳过"
                        result.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                                       "skip": step.skip, "group": step.group, "time": step.time,
                                       "curstring": curstring})
            return HttpResponse(json.dumps(result))


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
            step.time = time
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


def disasterdrill(request):
    if request.user.is_authenticated():
        return render(request, 'disasterdrill.html',
                      {'username': request.user.userinfo.fullname, "disasterdrillpage": True})
    else:
        return HttpResponseRedirect("/login")


def disasterdrilldata(request):
    if request.user.is_authenticated():
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                clientName = host.clientName
                clientGUID = host.clientGUID
                platform = host.platform
                appGroup = host.appGroup

                if host.hostType == "VMWARE":
                    alldataset = DataSet.objects.filter(clientGUID=clientGUID).exclude(status="9")
                    if len(alldataset) > 0:
                        for dataset in alldataset:
                            appGroup = dataset.appGroup
                            dataSetGUID = dataset.dataSetGUID
                            content = dataset.content
                            backupContentlist = []
                            if content != "" and content != None:
                                doc = parseString(content)
                                try:
                                    for node in doc.getElementsByTagName("backupContent"):
                                        a = len(node.getElementsByTagName("VM"))
                                        for vmlistnode in node.getElementsByTagName("VM"):
                                            try:
                                                backupContentlist.append(vmlistnode.childNodes[0].data)

                                            except:
                                                pass
                                except:
                                    pass
                            result.append(
                                {"clientName": clientName, "clientGUID": clientGUID, "type": host.hostType,
                                 "appGroup": appGroup, "dataSetGUID": dataSetGUID, "state": "正在运行",
                                 "backupContent": backupContentlist})
                else:
                    result.append(
                        {"clientName": clientName, "clientGUID": clientGUID, "platform": platform,
                         "type": host.hostType,
                         "appGroup": appGroup, "dataSetGUID": "", "state": "正在运行"})
        return HttpResponse(json.dumps({"data": result}))


def manualrecovery(request):
    if request.user.is_authenticated():
        return render(request, 'manualrecovery.html',
                      {'username': request.user.userinfo.fullname, "manualrecoverypage": True})
    else:
        return HttpResponseRedirect("/login")


def manualrecoverydata(request):
    if request.user.is_authenticated():
        result = []
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        if (len(allhost) > 0):
            for host in allhost:
                clientName = host.clientName
                clientGUID = host.clientGUID
                clientID = host.id
                platform = host.platform
                status = "否"
                if host.status == "1":
                    status = "是"
                agentTypeList = host.agentTypeList
                agentType = []
                try:
                    doc = parseString(agentTypeList)
                    for node in doc.getElementsByTagName("agentTypeList"):
                        for agenttypenode in node.getElementsByTagName("agentType"):
                            agentType.append(agenttypenode.childNodes[0].data)
                except:
                    pass

                if host.hostType == "VMWARE":
                    alldataset = DataSet.objects.filter(clientGUID=clientGUID).exclude(status="9")
                    if len(alldataset) > 0:
                        for dataset in alldataset:
                            appGroup = dataset.appGroup
                            dataSetID = dataset.id
                            content = dataset.content
                            backupContentlist = []
                            if content != "" and content != None:
                                doc = parseString(content)
                                try:
                                    for node in doc.getElementsByTagName("backupContent"):
                                        a = len(node.getElementsByTagName("VM"))
                                        for vmlistnode in node.getElementsByTagName("VM"):
                                            try:
                                                backupContentlist.append(vmlistnode.childNodes[0].data)

                                            except:
                                                pass
                                except:
                                    pass
                            result.append(
                                {"clientName": appGroup, "id": dataSetID, "type": host.hostType, "platform": platform,
                                 "state": status, "backupContent": backupContentlist})
                else:
                    result.append(
                        {"clientName": clientName, "id": clientID, "platform": platform, "type": host.hostType,
                         "state": status, "agentType": agentType})
        return HttpResponse(json.dumps({"data": result}))


def oraclerecovery(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        myhost = ClientHost.objects.filter(id=id)
        if len(myhost) > 0:
            if myhost[0].owernID == request.user.userinfo.userGUID:
                alldataset = DataSet.objects.filter(clientGUID=myhost[0].clientGUID, agentType='ORACLE').exclude(
                    status="9")
                if len(alldataset) > 0:
                    allhost = ClientHost.objects.exclude(status="9").filter(Q(hostType="physical box") & (
                            Q(owernID=request.user.userinfo.userGUID) | Q(
                        userinfo__id=request.user.userinfo.id))).filter(
                        agentTypeList__contains="<agentType>ORACLE</agentType>")
                    destClient = []
                    for host in allhost:
                        destClient.append(host.clientName)
                    return render(request, 'oraclerecovery.html', {'username': request.user.userinfo.fullname,
                                                                   "instanceName": alldataset[0].instanceName,
                                                                   "clientName": myhost[0].clientName,
                                                                   "destClient": destClient,
                                                                   "manualrecoverypage": True})
    else:
        return HttpResponseRedirect("/index")


def dooraclerecovery(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sourceClient = request.POST.get('sourceClient', '')
            destClient = request.POST.get('destClient', '')
            restoreTime = request.POST.get('restoreTime', '')
            instanceName = request.POST.get('instanceName', '')

            oraRestoreOperator = {"restoreTime": restoreTime, "restorePath": None}

            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            if cvAPI.restoreOracleBackupset(sourceClient, destClient, instanceName, oraRestoreOperator):
                return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
            else:
                return HttpResponse(u"恢复任务启动失败。" + cvAPI.msg)
        else:
            return HttpResponse("恢复任务启动失败。")


def oraclerecoverydata(request):
    if request.user.is_authenticated():
        result = []
        cvToken = CV_RestApi_Token()
        cvToken.login(info)
        cvAPI = CV_API(cvToken)
        clientName = request.GET.get('clientName', '')
        cvBackup = cvAPI.getBackupset(clientName, "Oracle Database")

        result = cvAPI.getJobList(cvBackup["clientId"], agentType=None, backupset=cvBackup["backupsetName"],
                                  type="backup")
        for node in result:
            try:
                x = time.localtime(float(node["LastTime"]))
                node["LastTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
            try:

                x = time.localtime(float(node["StartTime"]))
                node["StartTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
        return HttpResponse(json.dumps({"data": result}))


def mssqlrecovery(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        myhost = ClientHost.objects.filter(id=id)
        if len(myhost) > 0:
            if myhost[0].owernID == request.user.userinfo.userGUID:
                alldataset = DataSet.objects.filter(clientGUID=myhost[0].clientGUID, agentType='MSSQL').exclude(
                    status="9")
                if len(alldataset) > 0:
                    allhost = ClientHost.objects.exclude(status="9").filter(Q(hostType="physical box") &
                                                                            (Q(
                                                                                owernID=request.user.userinfo.userGUID) | Q(
                                                                                userinfo__id=request.user.userinfo.id))).filter(
                        agentTypeList__contains="<agentType>MSSQL</agentType>")
                    destClient = []
                    for host in allhost:
                        destClient.append(host.clientName)
                    return render(request, 'mssqlrecovery.html', {'username': request.user.userinfo.fullname,
                                                                  "instanceName": alldataset[0].instanceName,
                                                                  "clientName": myhost[0].clientName,
                                                                  "destClient": destClient, "manualrecoverypage": True})
    else:
        return HttpResponseRedirect("/index")


def domssqlrecovery(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            sourceClient = request.POST.get('sourceClient', '')
            destClient = request.POST.get('destClient', '')
            restoreTime = request.POST.get('restoreTime', '')
            instanceName = request.POST.get('instanceName', '')
            iscover = request.POST.get('iscover', '')
            overWrite = False
            if iscover == "TRUE":
                overWrite = True

            mssqlRestoreOperator = {"restoreTime": restoreTime, "overWrite": overWrite}
            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            if cvAPI.restoreMssqlBackupset(sourceClient, destClient, instanceName, mssqlRestoreOperator):
                return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
            else:
                return HttpResponse(u"恢复任务启动失败。" + cvAPI.msg)
            return HttpResponse("开发中...")
        else:
            return HttpResponse("恢复任务启动失败。")


def mssqlrecoverydata(request):
    if request.user.is_authenticated():
        result = []
        cvToken = CV_RestApi_Token()
        cvToken.login(info)
        cvAPI = CV_API(cvToken)
        clientName = request.GET.get('clientName', '')
        cvBackup = cvAPI.getBackupset(clientName, "SQL Server")

        result = cvAPI.getJobList(cvBackup["clientId"], agentType=None, backupset=cvBackup["backupsetName"],
                                  type="backup")
        for node in result:
            try:
                x = time.localtime(float(node["LastTime"]))
                node["LastTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
            try:

                x = time.localtime(float(node["StartTime"]))
                node["StartTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
        return HttpResponse(json.dumps({"data": result}))


def filerecovery(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        myhost = ClientHost.objects.filter(id=id)
        if len(myhost) > 0:
            if myhost[0].owernID == request.user.userinfo.userGUID:
                alldataset = DataSet.objects.filter(clientGUID=myhost[0].clientGUID, agentType='FILESYSTEM').exclude(
                    status="9")
                if len(alldataset) > 0:
                    allhost = ClientHost.objects.exclude(status="9").filter(Q(hostType="physical box") &
                                                                            (Q(
                                                                                owernID=request.user.userinfo.userGUID) | Q(
                                                                                userinfo__id=request.user.userinfo.id))).filter(
                        agentTypeList__contains="<agentType>FILESYSTEM</agentType>")
                    destClient = []
                    for host in allhost:
                        destClient.append(host.clientName)
                    return render(request, 'filerecovery.html', {'username': request.user.userinfo.fullname,
                                                                 "instanceName": alldataset[0].instanceName,
                                                                 "clientName": myhost[0].clientName,
                                                                 "destClient": destClient, "manualrecoverypage": True})
    else:
        return HttpResponseRedirect("/index")


def dofilerecovery(request):
    if request.user.is_authenticated():

        if request.method == 'POST':
            sourceClient = request.POST.get('sourceClient', '')
            destClient = request.POST.get('destClient', '')
            restoreTime = request.POST.get('restoreTime', '')
            instanceName = request.POST.get('instanceName', '')
            iscover = request.POST.get('iscover', '')
            mypath = request.POST.get('mypath', '')
            selectedfile = request.POST.get('selectedfile')
            sourceItemlist = selectedfile.split("*!-!*")
            client = ClientHost.objects.filter(clientName=sourceClient)
            if len(client) > 0:
                if 'LINUX' in client[0].platform.upper():
                    for i in range(len(sourceItemlist)):
                        if sourceItemlist[i] == '\\':
                            sourceItemlist[i] = '/'
                        else:
                            sourceItemlist[i] = sourceItemlist[i][1:-1]
            inPlace = True
            if mypath != "same":
                inPlace = False
            else:
                mypath = ""
            overWrite = False
            if iscover == "TRUE":
                overWrite = True

            for sourceItem in sourceItemlist:
                if sourceItem == "":
                    sourceItemlist.remove(sourceItem)

            fileRestoreOperator = {"restoreTime": restoreTime, "overWrite": overWrite, "inPlace": inPlace,
                                   "destPath": mypath, "sourcePaths": sourceItemlist, "OS Restore": False}

            cvToken = CV_RestApi_Token()
            cvToken.login(info)
            cvAPI = CV_API(cvToken)
            if cvAPI.restoreFSBackupset(sourceClient, destClient, "defaultBackupSet", fileRestoreOperator):
                return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
            else:
                return HttpResponse(u"恢复任务启动失败。" + cvAPI.msg)

        else:
            return HttpResponse("恢复任务启动失败。")


def filerecoverydata(request):
    if request.user.is_authenticated():
        result = []
        cvToken = CV_RestApi_Token()
        cvToken.login(info)
        cvAPI = CV_API(cvToken)
        clientName = request.GET.get('clientName', '')
        cvBackup = cvAPI.getBackupset(clientName, "File System")

        result = cvAPI.getJobList(cvBackup["clientId"], agentType=None, backupset=cvBackup["backupsetName"],
                                  type="backup")
        for node in result:
            try:
                x = time.localtime(float(node["LastTime"]))
                node["LastTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
            try:

                x = time.localtime(float(node["StartTime"]))
                node["StartTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
        return HttpResponse(json.dumps({"data": result}))


def getfiletree(request):
    id = request.POST.get('id', '')
    clientName = request.POST.get('clientName', '')
    allhost = ClientHost.objects.exclude(status="9").filter(clientName=clientName)
    treedata = []
    if len(allhost) > 0:
        clientID = int(allhost[0].clientID)
        cvToken = CV_RestApi_Token()
        cvToken.login(info)
        cvAPI = CV_API(cvToken)
        list = cvAPI.browse(clientID, "File System", None, id, False)
        for node in list:
            root = {}
            root["id"] = node["path"]
            root["pId"] = id
            root["name"] = node["path"]
            if node["DorF"] == "D":
                root["isParent"] = True
            else:
                root["isParent"] = False
            treedata.append(root)
        treedata = json.dumps(treedata)

    return HttpResponse(treedata)


def vmrecovery(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        mydataset = DataSet.objects.filter(id=id)
        if len(mydataset) > 0:
            if mydataset[0].owernID == request.user.userinfo.userGUID:
                allhost = ClientHost.objects.exclude(status="9").filter(Q(hostType="VMWARE") &
                                                                        (Q(owernID=request.user.userinfo.userGUID) | Q(
                                                                            userinfo__id=request.user.userinfo.id)))
                # allhost = ClientHost.objects.exclude(status="9").filter(hostType="VMWARE").exclude(clientGUID=mydataset[0].clientGUID)
                destClient = []
                vmlist = []
                dslist = []
                esxlist = []
                for host in allhost:
                    destClient.append(host.clientName)

                clientID = int(mydataset[0].clientID)
                cvToken = CV_RestApi_Token()
                cvToken.login(info)
                cvAPI = CV_API(cvToken)
                list = cvAPI.browse(clientID, "Virtual Server", mydataset[0].appGroup, None, False)

                for node in list:
                    vmlist.append({"name": node["displayName"], "id": node["name"]})

                VMWareDataStoreList = cvAPI.getVMWareDataStoreList(clientID)
                for VMWareDataStore in VMWareDataStoreList:
                    if {"text": VMWareDataStore["esxhost"], "value": VMWareDataStore["esxstrGUID"]} not in esxlist:
                        esxlist.append({"text": VMWareDataStore["esxhost"], "value": VMWareDataStore["esxstrGUID"]})
                    dslist.append({"text": VMWareDataStore["dataStoreName"],
                                   "value": VMWareDataStore["esxstrGUID"] + VMWareDataStore["dataStoreName"]})

                return render(request, 'vmrecovery.html',
                              {'username': request.user.userinfo.fullname, "appName": mydataset[0].appGroup,
                               "clientName": mydataset[0].clientName, "vmlist": vmlist, "esxlist": esxlist,
                               "dslist": dslist, "destClient": destClient, "manualrecoverypage": True})
            else:
                return HttpResponseRedirect("/manualrecovery")
        else:
            return HttpResponseRedirect("/manualrecovery")
    else:
        return HttpResponseRedirect("/index")


def getproxylist(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            result = []
            clientName = request.POST.get('clientName', '')
            allhost = ClientHost.objects.exclude(status="9").filter(hostType="VMWARE").filter(
                clientName=clientName)
            if (len(allhost) > 0):
                proxyClientID = allhost[0].proxyClientID
                if proxyClientID != "" and proxyClientID != None:
                    doc = parseString(proxyClientID)
                    for node in doc.getElementsByTagName("PROXYLIST"):
                        for proxylistnode in node.getElementsByTagName("PROXY"):
                            try:
                                proxy = ClientHost.objects.get(clientGUID=proxylistnode.childNodes[0].data)
                                result.append(proxy.clientName)
                            except:
                                pass
            return HttpResponse(json.dumps(result))


def dovmrecovery(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            appName = request.POST.get('appName', '')
            sourceClient = request.POST.get('sourceClient', '')
            sourceVMName = request.POST.get('sourceVMName', '')
            sourceVMGUID = request.POST.get('sourceVMGUID', '')
            newname = request.POST.get('newname', '')
            destClient = request.POST.get('destClient', '')
            proxyClient = request.POST.get('proxyClient', '')
            esxhost = request.POST.get('esxlist', '')
            dataStoreName = request.POST.get('dslist', '')
            disk = request.POST.get('disk', '')
            power = request.POST.get('power', '')
            iscover = request.POST.get('iscover', '')
            restoreTime = request.POST.get('restoreTime', '')
            mypower = False
            myiscover = False
            if power == "TRUE":
                mypower = True
            if iscover == "TRUE":
                myiscover = True
            hostname = ""
            username = ""

            allhost = ClientHost.objects.exclude(status="9").filter(hostType="VMWARE").filter(
                clientName=sourceClient)
            if len(allhost) > 0:
                creditInfo = allhost[0].creditInfo
                if creditInfo != "" and creditInfo != None:
                    doc = parseString(creditInfo)
                    for node in doc.getElementsByTagName("creditInfo"):
                        for hostnode in node.getElementsByTagName("HOST"):
                            hostname = hostnode.childNodes[0].data
                        for usernode in node.getElementsByTagName("USER"):
                            username = usernode.childNodes[0].data
                    vsaBrowseProxy = ""
                    proxyClientID = allhost[0].proxyClientID
                    if proxyClientID != "" and proxyClientID != None:
                        doc = parseString(proxyClientID)
                        for node in doc.getElementsByTagName("PROXYLIST"):
                            for proxylistnode in node.getElementsByTagName("PROXY"):
                                try:
                                    proxy = ClientHost.objects.get(clientGUID=proxylistnode.childNodes[0].data)
                                    vsaBrowseProxy = proxy.clientName
                                    break
                                except:
                                    pass

                    vmRestoreOperator = {"vsaClientName": sourceClient, "vmGUID": sourceVMGUID, "vmName": sourceVMName,
                                         "vsaBrowseProxy": vsaBrowseProxy,
                                         "vsaRestoreProxy": proxyClient, "vCenterHost": hostname,
                                         "vcenterUser": username, "DCName": esxhost, "esxHost": esxhost,
                                         "datastore": dataStoreName,
                                         "newVMName": newname, "diskOption": disk, "Power": mypower,
                                         "overWrite": myiscover, "restoreTime": restoreTime}
                    cvToken = CV_RestApi_Token()
                    cvToken.login(info)
                    cvAPI = CV_API(cvToken)
                    if cvAPI.restoreVMWareBackupset(sourceClient, destClient, appName, vmRestoreOperator):
                        return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
                    else:
                        return HttpResponse(u"恢复任务启动失败。" + cvAPI.msg)

                return HttpResponse("虚拟中心主机信息配置错误。")
            else:
                return HttpResponse("客户端不存在。")
        else:
            return HttpResponse("恢复任务启动失败。")


def vmrecoverydata(request):
    if request.user.is_authenticated():
        result = []
        cvToken = CV_RestApi_Token()
        cvToken.login(info)
        cvAPI = CV_API(cvToken)
        clientName = request.GET.get('clientName', '')
        cvBackup = cvAPI.getBackupset(clientName, "Virtual")

        result = cvAPI.getJobList(cvBackup["clientId"], agentType=None, backupset=cvBackup["backupsetName"],
                                  type="backup")
        for node in result:
            try:
                x = time.localtime(float(node["LastTime"]))
                node["LastTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
            try:

                x = time.localtime(float(node["StartTime"]))
                node["StartTime"] = time.strftime('%Y-%m-%d %H:%M:%S', x)
            except:
                pass
        return HttpResponse(json.dumps({"data": result}))


def report(request):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        allhost = ClientHost.objects.exclude(status="9").filter(
            Q(owernID=request.user.userinfo.userGUID) | Q(userinfo__id=request.user.userinfo.id))
        client = []
        for host in allhost:
            client.append(host.clientName)

        return render(request, "report.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "client": client, "reportpage": True})
    else:
        return HttpResponseRedirect("/login")


def reportdata(request):
    if request.user.is_authenticated():
        fail_status = ["Failed", "Killed", "Failed to Start"]
        if not is_connection_usable():
            connection.close()
        conn = pymssql.connect(host='cv-server\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
        cur = conn.cursor()
        result = []
        client = request.GET.get('client', '')
        type = request.GET.get('type', '')
        startdate = request.GET.get('startdate', '')
        enddate = request.GET.get('enddate', '')
        # joblist = Joblist.objects.all().order_by("-startdate")
        start_time = datetime.datetime.strptime(startdate, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
            seconds=1)
        # 默认
        exec_sql = """select * from [commserv].[dbo].[CommCellBackupInfo] where startdate between '{0}' and '{1}'""".format(
            start_time, end_time)

        if client != "" and type != "":
            exec_sql = """select * from [commserv].[dbo].[CommCellBackupInfo] where clientname='{0}' and idataagent='{1}' and startdate between '{2}' and '{3}'""".format(
                client, type, start_time, end_time)

        if client == "" and type != "":
            exec_sql = """select * from [commserv].[dbo].[CommCellBackupInfo] where idataagent='{0}' and startdate between '{1}' and '{2}'""".format(
                type, start_time, end_time)

        if client != "" and type == "":
            exec_sql = """select * from [commserv].[dbo].[CommCellBackupInfo] where clientname='{0}' and startdate between '{1}' and '{2}' """.format(
                client, start_time, end_time)
        cur.execute(exec_sql)
        joblist = cur.fetchall()

        for job in joblist:
            job_id = job[0]
            cur.execute(
                """SELECT SUM(sizeOnMedia) FROM [commserv].[dbo].[JMJobDataStats] where jobid={0}""".format(job_id))
            diskcapacity = cur.fetchall()
            if diskcapacity[0][0]:
                result.append({"jobid": job[0], "clientname": job[3], "idataagent": job[4],
                               "backuplevel": job[10], "backupset": job[6],
                               "startdate": job[18].strftime('%Y-%m-%d %H:%M:%S'),
                               "enddate": job[19].strftime('%Y-%m-%d %H:%M:%S'), "jobstatus": job[13],
                               "numbytesuncomp": str(job[23] / 1024 / 1024),
                               "diskcapacity": str(diskcapacity[0][0] / 1024 / 1024)})
        cur.close()
        conn.close()
        return HttpResponse(json.dumps({"data": result}))


def creatprocessrun(request):
    if request.user.is_authenticated():
        result = {}
        datasetid = request.POST.get('datasetid', '')
        processid = request.POST.get('processid', '')
        type = request.POST.get('type', '')
        try:
            datasetid = int(datasetid)
            processid = int(processid)
        except:
            raise Http404()
        process = Process.objects.filter(id=processid).exclude(state="9")
        if (len(process) <= 0):
            result["res"] = '流程启动失败，该流程不存在。'
        else:
            dataset = DataSet.objects.filter(id=0)
            if type == "Virtual Server":
                dataset = DataSet.objects.filter(id=datasetid).exclude(status="9")
            else:
                clienthost = ClientHost.objects.filter(id=datasetid).exclude(status="9")
                if (len(clienthost) > 0):
                    dataset = DataSet.objects.filter(clientGUID=clienthost[0].clientGUID, agentType=type).exclude(
                        status="9")
            if (len(dataset) <= 0):
                result["res"] = '流程启动失败，该应用已失效。'
            else:

                curprocessrun = ProcessRun.objects.filter(process=process[0], DataSet=dataset[0], state="RUN")
                if (len(curprocessrun) > 0):
                    result["res"] = '流程启动失败，该应用的另一个流程正在进行中，请勿重复启动。'
                else:
                    myprocessrun = ProcessRun()
                    myprocessrun.process = process[0]
                    myprocessrun.DataSet = dataset[0]
                    myprocessrun.starttime = datetime.datetime.now()
                    myprocessrun.creatuser = request.user.username
                    myprocessrun.state = "RUN"
                    myprocessrun.save()
                    mystep = process[0].step_set.exclude(state="9").filter(last=None)
                    if (len(mystep) <= 0):
                        result["res"] = '流程启动失败，没有找到可用步骤。'
                    else:
                        mysteprun = StepRun()
                        mysteprun.step = mystep[0]
                        mysteprun.starttime = datetime.datetime.now()
                        mysteprun.processrun = myprocessrun
                        mysteprun.state = "EDIT"
                        mysteprun.save()

                        myscript = mystep[0].script_set.exclude(state="9")
                        for script in myscript:
                            myscriptrun = ScriptRun()
                            myscriptrun.script = script
                            myscriptrun.steprun = mysteprun
                            myscriptrun.state = "EDIT"
                            myscriptrun.save()

                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = myprocessrun
                        myprocesstask.steprun = mysteprun
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = request.user.username
                        myprocesstask.receiveuser = request.user.username
                        myprocesstask.type = "RUN"
                        myprocesstask.state = "0"
                        myprocesstask.content = dataset[0].clientName + "的" + process[
                            0].name + " 流程已启动，请" + request.user.userinfo.fullname + "处理。"
                        myprocesstask.save()

                        result["res"] = "新增成功。"
                        result["data"] = process[0].url + "/" + str(myprocessrun.id)
        return HttpResponse(json.dumps(result))


def filecross(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        processrun = ProcessRun.objects.filter(id=id)
        if len(processrun):
            steprunid = 0
            processrunid = processrun[0].id
            task = processrun[0].processtask_set.filter(state="0")
            if len(task) > 0:
                try:
                    steprunid = task[0].steprun_id
                except:
                    pass
            datasetid = processrun[0].DataSet.id
            instanceName = processrun[0].DataSet.instanceName
            clientName = processrun[0].DataSet.clientName
            clientID = processrun[0].DataSet.clientID

            dataset = processrun[0].DataSet
            allhost = ClientHost.objects.exclude(status="9").exclude(id=dataset.id).filter(
                Q(hostType="physical box") &
                (Q(
                    owernID=request.user.userinfo.userGUID) | Q(
                    userinfo__id=request.user.userinfo.id))).filter(
                agentTypeList__contains="<agentType>FILESYSTEM</agentType>")
            destClient = []
            for host in allhost:
                destClient.append(host.clientName)

            steps = processrun[0].process.step_set.exclude(state="9")
            stepinfo = {}
            for index in range(len(steps)):
                step = steps[index]
                steprun = StepRun.objects.filter(step=step, processrun=processrun[0]).exclude(state="9")
                if len(steprun) > 0:
                    curstep = {"id": steprun[0].id, "state": steprun[0].state}
                    try:
                        doc = parseString(steprun[0].parameter)
                        for node in doc.getElementsByTagName("content"):
                            for child in node.childNodes:
                                curstep[child.nodeName] = child.childNodes[0].nodeValue
                    except:
                        pass
                    scriptruns = steprun[0].scriptrun_set.exclude(state="9")
                    curstep["scripts"] = scriptruns
                    stepinfo["step" + str(index + 1)] = curstep
            return render(request, 'filecross.html',
                          {'username': request.user.userinfo.fullname, "taskid": id, "processrunid": processrunid,
                           "steprunid": steprunid, "stepinfo": stepinfo,
                           "datasetid": datasetid,
                           "instanceName": instanceName,
                           "clientName": clientName, "clientID": clientID,
                           "destClient": destClient, "disasterdrillpage": True})
        else:
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/index")


def filecrossprevious(request):
    if request.user.is_authenticated():
        result = {}
        steprunid = request.POST.get('steprunid', '')
        try:
            steprunid = int(steprunid)
        except:
            raise Http404()
        steprun = StepRun.objects.filter(id=steprunid)
        if len(steprun) <= 0:
            result["res"] = '执行失败，该步骤配置异常。'
        else:
            steprun[0].state = "EDIT"
            steprun[0].save()

            task = steprun[0].processtask_set.filter(state="0")
            if len(task) > 0:
                task[0].endtime = datetime.datetime.now()
                task[0].state = "9"
                task[0].operator = request.user.username
                task[0].save()

            laststep = steprun[0].step.last
            mysteprun = None
            laststeprun = laststep.steprun_set.exclude(state="9").filter(processrun=steprun[0].processrun)
            if len(laststeprun) > 0:
                mysteprun = laststeprun[0]
                mysteprun.state = "EDIT"
                mysteprun.save()

                myscriptruns = mysteprun.scriptrun_set.exclude(state="9")
                for myscriptrun in myscriptruns:
                    # myscriptrun.state = "EDIT"
                    myscriptrun.save()

            else:
                mysteprun = StepRun()
                mysteprun.step = laststep
                mysteprun.processrun = steprun[0].processrun
                mysteprun.starttime = datetime.datetime.now()
                mysteprun.state = "EDIT"
                mysteprun.save()

                myscript = laststep.script_set.exclude(state="9")
                for script in myscript:
                    myscriptrun = ScriptRun()
                    myscriptrun.script = script
                    myscriptrun.steprun = mysteprun
                    myscriptrun.state = "EDIT"
                    myscriptrun.save()

            myprocesstask = ProcessTask()
            myprocesstask.processrun = steprun[0].processrun
            myprocesstask.steprun = mysteprun
            myprocesstask.starttime = datetime.datetime.now()
            myprocesstask.senduser = request.user.username
            myprocesstask.receiveuser = request.user.username
            myprocesstask.type = "RUN"
            myprocesstask.state = "0"
            myprocesstask.content = steprun[0].processrun.DataSet.clientName + "的" + steprun[
                0].processrun.process.name + "流程回退到“" + laststep.name + "”，请" + request.user.userinfo.fullname + "处理。"
            myprocesstask.save()

            result["res"] = "执行成功。"
            result["data"] = mysteprun.id
        return HttpResponse(json.dumps(result))


def filecrossnext(request):
    if request.user.is_authenticated():
        result = {}
        steprunid = request.POST.get('steprunid', '')
        stepindex = request.POST.get('stepindex', '')
        try:
            steprunid = int(steprunid)
        except:
            raise Http404()
        steprun = StepRun.objects.filter(id=steprunid)
        if len(steprun) <= 0:
            result["res"] = '执行失败，该步骤配置异常。'
        else:
            scriptruns = steprun[0].scriptrun_set.exclude(state="9").exclude(state="DONE")
            if len(scriptruns) > 0:
                steprun[0].state = "RUN"
                steprun[0].operator = ""
                # 异步执行当前步骤的所有脚本
                exec_script.delay(steprunid, request.user.username, request.user.userinfo.fullname)
            else:
                steprun[0].state = "DONE"
                # # 查看当前步骤是否有备份/恢复任务，若任务完成，写入DONE
                # jobid_from_xml = steprun[0].parameter
                # if jobid_from_xml:
                #     el = etree.XML(jobid_from_xml)
                #     jobid = ""
                #     try:
                #         jobid = el.xpath("//jobid/text()")
                #     except:
                #         pass
                #     if jobid:
                #         handle_job.delay(jobid, steprunid)

            if stepindex == "1":
                restoreTime = request.POST.get('restoreTime', '')
                steprun[0].parameter = "<content><restoreTime>" + restoreTime + "</restoreTime></content>"
            if stepindex == "3":
                destClient = request.POST.get('destClient', '')
                steprun[0].parameter = "<content><destClient>" + destClient + "</destClient></content>"
            if stepindex == "4":
                iscover = request.POST.get('iscover', '')
                mypath = request.POST.get('mypath', '')
                selectedfile = request.POST.get('selectedfile', '')
                steprun[
                    0].parameter = "<content><iscover>" + iscover + "</iscover><mypath>" + mypath + "</mypath><selectedfile>" + selectedfile + "</selectedfile></content>"
            if stepindex == "5":
                sourceClient = request.POST.get('sourceClient', '')
                destClient = request.POST.get('destClient', '')
                restoreTime = request.POST.get('restoreTime', '')
                instanceName = request.POST.get('instanceName', '')
                iscover = request.POST.get('iscover', '')
                mypath = request.POST.get('mypath', '')
                selectedfile = request.POST.get('selectedfile')
                sourceItemlist = selectedfile.split("*!-!*")
                client = ClientHost.objects.filter(clientName=sourceClient)
                if len(client) > 0:
                    if 'LINUX' in client[0].platform.upper():
                        for i in range(len(sourceItemlist)):
                            if sourceItemlist[i] == '\\':
                                sourceItemlist[i] = '/'
                            else:
                                sourceItemlist[i] = sourceItemlist[i][1:-1]
                inPlace = True
                if mypath != "same":
                    inPlace = False
                else:
                    mypath = ""
                overWrite = False
                if iscover == "TRUE":
                    overWrite = True

                for sourceItem in sourceItemlist:
                    if sourceItem == "":
                        sourceItemlist.remove(sourceItem)

                fileRestoreOperator = {"restoreTime": restoreTime, "overWrite": overWrite, "inPlace": inPlace,
                                       "destPath": mypath, "sourcePaths": sourceItemlist, "OS Restore": False}
                cvToken = CV_RestApi_Token()
                cvToken.login(info)
                cvAPI = CV_API(cvToken)
                jobid = cvAPI.restoreFSBackupset(sourceClient, destClient, "defaultBackupSet", fileRestoreOperator)
                if jobid:
                    if jobid > 0:
                        steprun[0].parameter = "<content><jobid>" + str(jobid) + "</jobid></content>"
                        steprun[0].state = "RUN"
                        steprun[0].operator = ""
                        handle_job.delay(jobid, steprunid)
                    else:
                        result["res"] = '执行失败，恢复任务启动失败。' + cvAPI.msg
                        return HttpResponse(json.dumps(result))
                else:
                    result["res"] = '执行失败，恢复任务启动失败。' + cvAPI.msg
                    return HttpResponse(json.dumps(result))

            if stepindex == "6":
                checkservice = request.POST.get('checkservice', '')
                steprun[0].parameter = "<content><checkservice>" + checkservice + "</checkservice></content>"
            steprun[0].endtime = datetime.datetime.now()
            steprun[0].save()

            task = steprun[0].processtask_set.filter(state="0")
            if len(task) > 0:
                task[0].endtime = datetime.datetime.now()
                task[0].state = "1"
                task[0].operator = request.user.username
                task[0].save()

            nextstep = steprun[0].step.next.exclude(state="9")
            if len(nextstep) > 0:
                mysteprun = None
                scriptrunslist = []
                nextsteprun = nextstep[0].steprun_set.exclude(state="9").filter(processrun=steprun[0].processrun)
                if len(nextsteprun) > 0:
                    mysteprun = nextsteprun[0]
                    mysteprun.state = "EDIT"
                    mysteprun.save()

                    myscriptruns = mysteprun.scriptrun_set.exclude(state="9")
                    for myscriptrun in myscriptruns:
                        myscriptrun.state = "EDIT"
                        myscriptrun.save()

                else:
                    mysteprun = StepRun()
                    mysteprun.step = nextstep[0]
                    mysteprun.processrun = steprun[0].processrun
                    mysteprun.starttime = datetime.datetime.now()
                    mysteprun.state = "EDIT"
                    mysteprun.save()

                    myscript = nextstep[0].script_set.exclude(state="9")
                    for script in myscript:
                        myscriptrun = ScriptRun()
                        myscriptrun.script = script
                        myscriptrun.steprun = mysteprun
                        myscriptrun.state = "EDIT"
                        myscriptrun.save()
                        scriptrunslist.append({"script_id": myscriptrun.id, "script_code": myscriptrun.script.code})
                if len(scriptruns) > 0:
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun = steprun[0].processrun
                    myprocesstask.steprun = steprun[0]
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = request.user.username
                    myprocesstask.receiveuser = request.user.username
                    myprocesstask.type = "RUN"
                    myprocesstask.state = "0"
                    myprocesstask.content = steprun[0].processrun.DataSet.clientName + "的" + steprun[
                        0].processrun.process.name + "流程“" + steprun[0].step.name + "”正在执行脚本，点击查看。"
                    myprocesstask.save()
                else:
                    if stepindex == "5":
                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = steprun[0].processrun
                        myprocesstask.steprun = mysteprun
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = request.user.username
                        myprocesstask.receiveuser = request.user.username
                        myprocesstask.type = "RUN"
                        myprocesstask.state = "0"
                        myprocesstask.content = steprun[0].processrun.DataSet.clientName + "的" + steprun[
                            0].processrun.process.name + "流程“" + steprun[0].step.name + "”正在执行，点击查看。"
                        myprocesstask.save()
                    else:
                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = steprun[0].processrun
                        myprocesstask.steprun = mysteprun
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.senduser = request.user.username
                        myprocesstask.receiveuser = request.user.username
                        myprocesstask.type = "RUN"
                        myprocesstask.state = "0"
                        myprocesstask.content = steprun[0].processrun.DataSet.clientName + "的" + steprun[
                            0].processrun.process.name + "流程进行到“" + nextstep[
                                                    0].name + "”，请" + request.user.userinfo.fullname + "处理。"
                        myprocesstask.save()

                result["res"] = "执行成功。"
                if len(scriptruns) > 0:
                    result["data"] = steprun[0].id
                else:
                    result["data"] = mysteprun.id
                result["nextdata"] = mysteprun.id
                result["scriptrunslist"] = scriptrunslist
                result["steprunstate"] = steprun[0].state
        return HttpResponse(json.dumps(result))


def filecrossfinish(request):
    if request.user.is_authenticated():
        result = {}
        steprunid = request.POST.get('steprunid', '')
        try:
            steprunid = int(steprunid)
        except:
            raise Http404()
        steprun = StepRun.objects.filter(id=steprunid)
        if len(steprun) <= 0:
            result["res"] = '执行失败，该步骤配置异常。'
        else:
            steprun[0].state = "DONE"
            checkapp = request.POST.get('checkapp', '')
            steprun[0].parameter = "<content><checkapp>" + checkapp + "</checkapp></content>"
            steprun[0].endtime = datetime.datetime.now()
            steprun[0].save()

            task = steprun[0].processtask_set.filter(state="0")
            if len(task) > 0:
                task[0].endtime = datetime.datetime.now()
                task[0].state = "1"
                task[0].operator = request.user.username
                task[0].save()

            myprocessrun = steprun[0].processrun
            myprocessrun.endtime = datetime.datetime.now()
            myprocessrun.state = "DONE"
            myprocessrun.save()
            result["res"] = "执行成功。"
        return HttpResponse(json.dumps(result))


def getsinglevm(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        vmlist = VmResource.objects.exclude(state="9").exclude(vm_type='模板虚机').filter(id=id)
        if (len(vmlist) > 0):
            resource = vmlist[0]
            id = resource.id
            name = resource.name
            pool_id = resource.pool_id
            specifications = resource.specifications
            description = resource.description
            instance_name = resource.template_name  # ...对应的name
            system = resource.system
            template_id = resource.template_id
            template_name = resource.template.name
            template_template_name = resource.template.template_name
            template_uuid = resource.template.uuid
            uuid = resource.uuid

            resourcepool = ResourcePool.objects.filter(id=pool_id)[0]
            certificate = resourcepool.certificate
            pool_name = resourcepool.name
            # 从资源池中获取certificate,并获取ip,user,password

            doc = parseString(certificate)
            ip = ""
            username = ""
            password = ""
            cert_name = ""
            for node in doc.getElementsByTagName("CERT_LIST"):
                for hostnode in node.getElementsByTagName("CERT"):
                    ip = hostnode.getAttribute("ip")
                    username = hostnode.getAttribute("username")
                    password = hostnode.getAttribute("password")
                    datacenter = hostnode.getAttribute("datacenter")
                    cluster = hostnode.getAttribute("cluster")

            doc2 = parseString(specifications)
            for node in doc2.getElementsByTagName("SPEC_LIST"):
                cpu = node.getAttribute("cpu")
                memory = node.getAttribute("memory")
                disk = node.getAttribute("disk")
                vmip = node.getAttribute("vmip")
                hostname = node.getAttribute("hostname")
                clone = node.getAttribute("clone")

            result = {"id": id, "name": name, "description": description,
                      "cpu": cpu, "memory": memory, "datacenter": datacenter, "cluster": cluster, "ip": vmip,
                      "hostname": hostname,
                      "disks": disk, "instance_name": instance_name, "template_id": template_id, "clone": clone,
                      "template_name": template_name, "template_template_name": template_template_name,
                      "template_uuid": template_uuid, "system": system, "pool_id": pool_id,
                      "pool_name": pool_name, "uuid": uuid}
        return HttpResponse(json.dumps(result))


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
                endtime = scriptrun_obj.starttime.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            script_info = {
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


def exec_script_by_hand(request):
    if request.user.is_authenticated():
        current_step_id = request.POST.get('steprunid', '')
        selected_script_id = request.POST.get('scriptid', '')
        scriptruns = ScriptRun.objects.filter(id=selected_script_id)[0]
        steprun = StepRun.objects.filter(id=current_step_id)
        steprun = steprun[0]
        cmd = r"{0}".format(scriptruns.script.scriptpath + scriptruns.script.filename)
        ip = scriptruns.script.ip
        username = scriptruns.script.username
        password = scriptruns.script.password
        script_type = scriptruns.script.type
        system_tag = ""
        if script_type == "SSH":
            system_tag = "Linux"
        if script_type == "BAT":
            system_tag = "Windows"
        rm_obj = remote.ServerByPara(cmd, ip, username, password, system_tag)  # 服务器系统从视图中传入
        scriptruns.starttime = datetime.datetime.now()
        result = rm_obj.run()
        script.result = result["exec_tag"]
        # 处理脚本执行失败问题
        if result["exec_tag"] == 1:
            print("当前脚本执行失败,结束任务!")  # 2.写入错误信息至operator
            scriptruns.operator = result['data']
            scriptruns.save()
            steprun.state = "ERROR"
            steprun.save()
        scriptruns.endtime = datetime.datetime.now()
        scriptruns.operator = ""
        scriptruns.state = "DONE"
        scriptruns.save()
        return JsonResponse({"data": result})


def ignore_current_script(request):
    if request.user.is_authenticated():
        selected_script_id = request.POST.get('scriptid', '')
        scriptruns = ScriptRun.objects.filter(id=selected_script_id)[0]
        scriptruns.state = "IGNORE"
        scriptruns.save()
        return JsonResponse({"data": "成功忽略当前脚本"})


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

        group_name = ""
        if child.group:
            group_id = child.group
            group_name = Group.objects.filter(id=group_id)[0].name

        all_groups = Group.objects.exclude(state="9")
        group_string = ""
        for group in all_groups:
            id_name_plus = str(group.id) + "+" + str(group.name) + "&"
            group_string += id_name_plus

        node["data"] = {"time": child.time, "approval": child.approval, "skip": child.skip, "group_name": group_name,
                        "group": child.group, "scripts": script_string, "allgroups": group_string}
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
        group_string = ""
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
                root["text"] = rootnode.name
                root["id"] = rootnode.id
                group_name = ""
                if rootnode.group:
                    group_id = rootnode.group
                    group_name = Group.objects.filter(id=group_id)[0].name

                root["data"] = {"time": rootnode.time, "approval": rootnode.approval, "skip": rootnode.skip,
                                "allgroups": group_string, "group": rootnode.group, "group_name": group_name,
                                "scripts": script_string, "errors": errors, "title": title}
                root["children"] = get_step_tree(rootnode, selectid)
                treedata.append(root)
        process = {}
        process["text"] = process_name
        process["data"] = {"allgroups": group_string, "verify": "first_node"}
        process["children"] = treedata
        return JsonResponse({"treedata": process})
    else:
        return HttpResponseRedirect("/login")


def step_tree_index(request):
    if request.user.is_authenticated():
        processes = Process.objects.exclude(state="9").order_by("sort")
        processlist = []
        for process in processes:
            processlist.append({"id": process.id, "code": process.code, "name": process.name})
        return render(request, 'processconfig.html',
                      {'username': request.user.userinfo.fullname, "step_tree_index_page": True,
                       "processlist": processlist})


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
        for group in all_groups:
            group_info_dict = {
                "group_id": group.id,
                "group_name": group.name,
            }
            all_group_list.append(group_info_dict)
        return JsonResponse({"data": all_group_list})


def falconstorswitch(request):
    if request.user.is_authenticated():
        return render(request, 'falconstorswitch.html',
                      {'username': request.user.userinfo.fullname, "falconstorpage": True})
    else:
        return HttpResponseRedirect("/login")


def falconstorswitchdata(request):
    if request.user.is_authenticated():
        result = []
        allprocess = Process.objects.exclude(state="9").filter(type="falconstor")
        if (len(allprocess) > 0):
            for process in allprocess:
                code = process.code
                name = process.name
                rto = process.rto
                rpo = process.rpo
                remark = process.remark
                result.append(
                    {"code": code, "name": name, "rto": rto, "rpo": rpo,
                     "remark": remark, "id": process.id})
        return HttpResponse(json.dumps({"data": result}))


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
        process = Process.objects.filter(id=processid).exclude(state="9")
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
                            # print(1)
                            myscriptrun = ScriptRun()
                            myscriptrun.script = script
                            myscriptrun.steprun = mysteprun
                            myscriptrun.state = "EDIT"
                            myscriptrun.save()

                    allgroup = process[0].step_set.exclude(state="9").exclude(Q(approval="0") | Q(approval="")).values(
                        "group").distinct()  # 当前预案下需要签字的组,但一个对象只发送一次task

                    if process[0].sign == "1" and len(allgroup) > 0:  # 如果预案流程已经启动,发送签字tasks
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
                                myprocesstask.content = "管理员将启动流程“" + myprocessrun.process.name + "”，请" + groupname + "签字。"
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
                            myprocesstask.type = "RUN"
                            myprocesstask.state = "0"
                            myprocesstask.receiveuser = request.user.username
                            myprocesstask.senduser = request.user.username
                            myprocesstask.content = myprocess.name + " 流程已启动，点击查看。"
                            myprocesstask.save()

                            exec_process.delay(myprocessrun.id)
                            result["res"] = "新增成功。"
                            result["data"] = process[0].url + "/" + str(myprocessrun.id)
        return HttpResponse(json.dumps(result))


def falconstor(request, offset):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()
        return render(request, 'falconstor.html',
                      {'username': request.user.userinfo.fullname, "process": id, "falconstorpage": True})
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
            operator = steprunlist[0].operator
            parameter = steprunlist[0].parameter
            runresult = steprunlist[0].result
            explain = steprunlist[0].explain
            state = steprunlist[0].state
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
            scripts.append({"id": script.id, "code": script.code, "name": script.name, "runscriptid": runscriptid,
                            "scriptstarttime": scriptstarttime,
                            "scriptendtime": scriptendtime, "scriptoperator": scriptoperator,
                            "scriptrunresult": scriptrunresult, "scriptexplain": scriptexplain,
                            "scriptrunlog": scriptrunlog, "scriptstate": scriptstate})
        childresult.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                            "skip": step.skip, "group": step.group, "time": step.time, "runid": runid,
                            "starttime": starttime,
                            "endtime": endtime, "operator": operator, "parameter": parameter, "runresult": runresult,
                            "explain": explain, "state": state, "scripts": scripts,
                            "children": getchildrensteps(processrun, step)})
    return childresult


def getrunsetps(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            result = []
            processrun = request.POST.get('process', '')
            try:
                processrun = int(processrun)
            except:
                raise Http404()
            processruns = ProcessRun.objects.exclude(state="9").filter(id=processrun)
            if len(processruns) > 0:
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
                        operator = steprunlist[0].operator
                        parameter = steprunlist[0].parameter
                        runresult = steprunlist[0].result
                        explain = steprunlist[0].explain
                        state = steprunlist[0].state
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

                    result.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                                   "skip": step.skip, "group": step.group, "time": step.time, "runid": runid,
                                   "starttime": starttime,
                                   "endtime": endtime, "operator": operator, "parameter": parameter,
                                   "runresult": runresult,
                                   "explain": explain, "state": state, "scripts": scripts,
                                   "children": getchildrensteps(processruns[0], step)})

            return HttpResponse(json.dumps(result))


def falconstorcontinue(request):
    if request.user.is_authenticated():
        result = {}
        process = request.POST.get('process', '')
        try:
            process = int(process)
        except:
            raise Http404()
        exec_process.delay(process)
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
                myprocesstask.type = "RUN"
                myprocesstask.state = "0"
                myprocesstask.content = myprocess.name + " 流程已启动，点击查看。"
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.receiveuser = request.user.username
                myprocesstask.senduser = request.user.username
                myprocesstask.save()

                exec_process.delay(myprocessrun.id)
                result["res"] = "签字成功,同时启动流程。"
                result["data"] = myprocess.url + "/" + str(myprocessrun.id)
            else:
                result["res"] = "签字成功。"
        except:
            result["res"] = "流程启动失败，请于管理员联系。"
        return JsonResponse(result)


from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
# 注册中文
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import collections


def custom_pdf_report(request):
    """
    由于reportlab模块中styles.getSampleStyleSheet方法中的对象只能生成一次，所以这里选择将其中Heading1-5对象中的属性消除，
    再添加适当缩进属性作为新的style来处理；
    :param request: processrun_id, process_id
    :return: response
    """
    if request.user.is_authenticated():
        # 请求参数
        processrun_id = request.GET.get("processrunid", "")
        process_id = request.GET.get("processid", "")
        # 注册宋体
        current_path = os.getcwd()
        fsong_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + "fonts" + os.sep + "fangsong.ttf"
        pdfmetrics.registerFont(TTFont('fsong', r'{0}'.format(fsong_path)))

        # 生成pdf对象
        response = HttpResponse(content_type='application/pdf')
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            rightMargin=72,
            leftMargin=72,
            topMargin=30,
            bottomMargin=72)
        styles = getSampleStyleSheet()

        # 获取当前流程对象
        process_run_objs = ProcessRun.objects.filter(id=processrun_id)
        if process_run_objs:
            process_run_obj = process_run_objs[0]
        else:
            return Http404()

        # 构建元素列表
        elements = []

        # 设置段落样式
        font_style_title = styles['Title']
        font_style_title.fontName = "fsong"
        font_style_title.fontSize = 40  # 字体大小

        # 报表封页文字
        title_xml = "飞康自动化恢复流程"
        abstract_xml = "切换报告"

        manager_xml = "{0}".format(request.user.userinfo.fullname)
        report_time = datetime.datetime.now().strftime("%Y-%m-%d")

        # 添加元素，以及换行
        elements.append(Spacer(0, 5 * cm))
        elements.append(Paragraph(title_xml, font_style_title))
        elements.append(Spacer(0, 0.5 * cm))
        font_style_title.fontSize = 35
        elements.append(Paragraph(abstract_xml, font_style_title))
        elements.append(Spacer(0, 2 * cm))
        font_style_title.fontSize = 20
        elements.append(Paragraph(manager_xml, font_style_title))
        elements.append(Spacer(0, 0.1 * cm))
        elements.append(Paragraph(report_time, font_style_title))
        elements.append(Spacer(0, 14 * cm))

        font_style_ele = styles["Heading3"]
        font_style_ele.fontName = "fsong"
        font_style_ele.fontSize = 12
        font_style_ele.leading = 0
        font_style_ele.spaceBefore = 0
        font_style_ele.spaceAfter = 0

        elements.append(Spacer(0, 0.5 * cm))
        ele_xml01 = "一、切换概述"
        elements.append(Paragraph(ele_xml01, font_style_ele))
        elements.append(Spacer(0, 1 * cm))

        if process_run_obj:
            # 切换概述节点下内容,有序字典中存放
            first_el_dict = collections.OrderedDict()

            start_time = process_run_obj.starttime
            end_time = process_run_obj.endtime
            create_user = process_run_obj.creatuser
            users = User.objects.filter(username=create_user)
            if users:
                create_user = users[0].userinfo.fullname
            else:
                return Http404()
            run_reason = process_run_obj.run_reason

            first_el_dict["开始时间:"] = r"<para><u>{0}</u></para>".format(
                start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "")
            first_el_dict["结束时间:"] = r"<para><u>{0}</u></para>".format(
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

                first_el_dict["RTO:"] = r"<para><u>{0}</u></para>".format(delta_time)
            else:
                first_el_dict["RTO:"] = r"<para><u>{0}</u></para>".format("")
            first_el_dict["发起人:"] = r"<para><u>{0}</u></para>".format(create_user)

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

                first_el_dict["签字人:"] = r"<para><u>{0}</u></para>".format(receiveusers[:-1])

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

            first_el_dict["参与人:"] = r"<para><u>{0}</u></para>".format(operators[:-1])
            first_el_dict["切换原因:"] = r"<para><u>{0}</u></para>".format(run_reason)

            # 有序字典中内容写入pdf
            for key, value in first_el_dict.items():
                if not key:
                    key = ""
                if not value:
                    value = ""

                key_style01 = styles["Heading5"]
                key_style01.fontName = "fsong"
                key_style01.fontSize = 12
                key_style01.wordWrap = "CJK"
                key_style01.leading = 0
                key_style01.spaceBefore = 0
                key_style01.spaceAfter = 0
                key_style01.firstLineIndent = 30

                value_style01 = styles["Italic"]
                value_style01.fontName = "fsong"
                value_style01.fontSize = 12
                value_style01.wordWrap = "CJK"
                value_style01.firstLineIndent = 60

                elements.append(Paragraph(key, key_style01))
                elements.append(Spacer(0, 0.5 * cm))
                elements.append(Paragraph(value, value_style01))

                elements.append(Spacer(0, 0.2 * cm))

            ele_xml02 = "二、步骤详情"
            elements.append(Paragraph(ele_xml02, font_style_ele))
            elements.append(Spacer(0, 1 * cm))

            pnode_steplist = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
                pnode_id=None)

            for num, pstep in enumerate(pnode_steplist):
                second_el_dict = collections.OrderedDict()
                el_title = "{0}.{1}".format(num + 1, pstep.name)
                el_style = styles["Heading5"]
                el_style.fontName = "fsong"
                el_style.fontSize = 12
                elements.append(Paragraph(el_title, el_style))
                elements.append(Spacer(0, 1 * cm))

                el_style.fontSize = 12

                pnode_steprun = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id).filter(
                    step=pstep)
                if pnode_steprun:
                    second_el_dict["开始时间:"] = pnode_steprun[0].starttime.strftime("%Y-%m-%d %H:%M:%S") if pnode_steprun[
                        0].starttime else ""
                    second_el_dict["结束时间:"] = pnode_steprun[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if pnode_steprun[
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

                        second_el_dict["RTO:"] = delta_time
                    else:
                        second_el_dict["RTO:"] = ""

                # ...需要审批时，添加负责人
                if pstep.approval == "1":
                    users = User.objects.filter(username=pnode_steprun[0].operator)
                    if users:
                        operator = users[0].userinfo.fullname
                        second_el_dict["负责人:"] = operator

                for key, value in second_el_dict.items():
                    if not key:
                        key = ""
                    if not value:
                        value = ""

                    dict_style = styles["Heading1"]
                    dict_style.fontName = "fsong"
                    dict_style.fontSize = 12
                    dict_style.leading = 0
                    dict_style.spaceAfter = 0
                    dict_style.firstLineIndent = 45
                    dict_data = r"<para>{0}<u>{1}</u></para>".format(key, value)

                    elements.append(Paragraph(dict_data, dict_style))
                    elements.append(Spacer(0, 0.5 * cm))

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
                if current_scripts:
                    script_title_style = styles["Heading1"]
                    script_title_style.fontName = "fsong"
                    script_title_style.fontSize = 12
                    script_title = "<para>脚本:</para>"
                    elements.append(Paragraph(script_title, script_title_style))
                    elements.append(Spacer(0, 0.5 * cm))

                    for snum, current_script in enumerate(current_scripts):
                        script_el_dict = collections.OrderedDict()
                        # title
                        script_title = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                        script_title01_style = styles["Heading4"]
                        script_title01_style.fontName = "fsong"
                        script_title01_style.fontSize = 12
                        script_title01_style.wordWrap = "CJK"
                        script_title01_style.leading = 0
                        script_title01_style.spaceBefore = 0
                        script_title01_style.spaceAfter = 0
                        script_title01_style.firstLineIndent = 60

                        elements.append(Paragraph(script_title, script_title01_style))
                        elements.append(Spacer(0, 0.5 * cm))
                        # content
                        steprun_id = pnode_steprun[0].id
                        script_id = current_script.id
                        current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id, script_id=script_id)
                        if current_scriptrun_obj:
                            script_el_dict["开始时间:"] = current_scriptrun_obj[0].starttime.strftime(
                                "%Y-%m-%d %H:%M:%S") if \
                                current_scriptrun_obj[0].starttime else ""
                            script_el_dict["结束时间:"] = current_scriptrun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if \
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

                                script_el_dict["RTO:"] = delta_time
                            else:
                                script_el_dict["RTO:"] = ""

                            state = current_scriptrun_obj[0].state
                            if state in state_dict.keys():
                                script_el_dict["状态:"] = state_dict[state]
                            else:
                                script_el_dict["状态:"] = ""
                            script_el_dict["执行结果:"] = current_scriptrun_obj[0].explain

                            for key, value in script_el_dict.items():
                                if not key:
                                    key = ""
                                if not value:
                                    value = ""
                                script_data = r"<para>{0}<u>{1}</u></para>".format(key, value)

                                script_content_style = styles["BodyText"]
                                script_content_style.fontName = "fsong"
                                script_content_style.fontSize = 12
                                script_content_style.wordWrap = "CJK"
                                script_content_style.firstLineIndent = 75

                                elements.append(Paragraph(script_data, script_content_style))
                                elements.append(Spacer(0, 0.1 * cm))

                # 子步骤下相关内容
                p_id = pstep.id
                inner_steps = Step.objects.exclude(state="9").filter(process_id=process_id).order_by("sort").filter(
                    pnode_id=p_id)

                if inner_steps:
                    for num, step in enumerate(inner_steps):
                        el_title = "{0}){1}".format(num + 1, step.name)
                        el_style = styles["Italic"]
                        el_style.fontName = "fsong"
                        el_style.fontSize = 12

                        elements.append(Paragraph(el_title, el_style))
                        elements.append(Spacer(0, 0.2 * cm))

                        el_style.fontSize = 12
                        steprun_obj = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id).filter(
                            step=step)
                        if steprun_obj:
                            second_el_dict["开始时间:"] = steprun_obj[0].starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                                steprun_obj[0].starttime else ""
                            second_el_dict["结束时间:"] = steprun_obj[0].endtime.strftime("%Y-%m-%d %H:%M:%S") if \
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

                                second_el_dict["RTO:"] = delta_time
                            else:
                                second_el_dict["RTO:"] = ""

                            # ...需要审批时
                            if step.approval == "1":
                                users = User.objects.filter(username=steprun_obj[0].operator)
                                if users:
                                    operator = users[0].userinfo.fullname
                                    second_el_dict["负责人:"] = operator

                            for key, value in second_el_dict.items():
                                if not key:
                                    key = ""
                                if not value:
                                    value = ""

                                dict_style = styles["Heading2"]
                                dict_style.fontName = "fsong"
                                dict_style.fontSize = 12
                                dict_style.leading = 0
                                dict_style.spaceBefore = 0
                                dict_style.spaceAfter = 0
                                dict_style.firstLineIndent = 72

                                dict_data = r"""<para>{0}<u>{1}</u></para>""".format(key, value)

                                elements.append(Paragraph(dict_data, dict_style))
                                elements.append(Spacer(0, 0.7 * cm))

                            # 当前步骤下脚本
                            current_scripts = Script.objects.exclude(state="9").filter(step_id=step.id)
                            if current_scripts:
                                script_title_style = styles["Heading2"]
                                script_title_style.fontName = "fsong"
                                script_title_style.fontSize = 12

                                script_title = "<para>脚本:</para>"
                                elements.append(Paragraph(script_title, script_title_style))
                                elements.append(Spacer(0, 0.5 * cm))
                                for snum, current_script in enumerate(current_scripts):
                                    script_el_dict = collections.OrderedDict()
                                    # title
                                    script_title = "{0}.{1}".format("i" * (snum + 1), current_script.name)
                                    script_title01_style = styles["Bullet"]
                                    script_title01_style.fontName = "fsong"
                                    script_title01_style.firstLineIndent = 90
                                    script_title01_style.fontSize = 12

                                    elements.append(Paragraph(script_title, script_title01_style))
                                    elements.append(Spacer(0, 0.2 * cm))
                                    # content
                                    steprun_id = steprun_obj[0].id
                                    script_id = current_script.id
                                    current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id,
                                                                                     script_id=script_id)
                                    script_el_dict["开始时间:"] = current_scriptrun_obj[0].starttime.strftime(
                                        "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj[0].starttime else ""
                                    script_el_dict["结束时间:"] = current_scriptrun_obj[0].endtime.strftime(
                                        "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj[0].endtime else ""

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

                                        script_el_dict["RTO:"] = delta_time
                                    else:
                                        script_el_dict["RTO:"] = ""

                                    state = current_scriptrun_obj[0].state
                                    if state in state_dict.keys():
                                        script_el_dict["状态:"] = state_dict[state]
                                    else:
                                        script_el_dict["状态:"] = ""

                                    script_el_dict["执行结果:"] = current_scriptrun_obj[0].explain
                                    for key, value in script_el_dict.items():
                                        if not key:
                                            key = ""
                                        if not value:
                                            value = ""
                                        script_data = r"<para>{0}<u>{1}</u></para>".format(key, value)

                                        script_content_style = styles['Normal']
                                        script_content_style.fontName = "fsong"
                                        script_content_style.fontSize = 12  # 字体大小
                                        script_content_style.wordWrap = "CJK"
                                        script_content_style.firstLineIndent = 105

                                        elements.append(Paragraph(script_data, script_content_style))
                                        elements.append(Spacer(0, 0.2 * cm))
                    elements.append(Spacer(0, 0.5 * cm))

            doc.multiBuild(elements)
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response


def falconstorsearch(request):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        all_processes = Process.objects.exclude(state="9")
        processname_list = []
        for process in all_processes:
            processname_list.append(process.name)

        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
        }
        return render(request, "falconstorsearch.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "processname_list": processname_list, "state_dict": state_dict, "falconstorsearchpage": True})
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
        all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time]).order_by("-starttime")

        if runperson:
            if processname != "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                                   process__name=processname,
                                                                                   state=runstate, creatuser=runperson).order_by("-starttime")
            if processname == "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                                   state=runstate, creatuser=runperson).order_by("-starttime")
            if processname != "" and runstate == "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                               process__name=processname, creatuser=runperson).order_by("-starttime")
        else:
            if processname != "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                                   process__name=processname,
                                                                                   state=runstate).order_by("-starttime")
            if processname == "" and runstate != "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                                   state=runstate).order_by("-starttime")
            if processname != "" and runstate == "":
                all_processrun_objs = ProcessRun.objects.exclude(state="9").filter(starttime__range=[start_time, end_time],
                                                                               process__name=processname).order_by("-starttime")
        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
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
