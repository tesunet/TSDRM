# 监控图表：仪表盘、灾备基础框架
from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required

from .tasks import *
from .views import getpagefuns
from faconstor.api import SQLApi
from .public import (
    get_credit_info
)

import datetime
import pythoncom
from ping3 import ping
from collections import OrderedDict
import cx_Oracle
import pymysql

pythoncom.CoInitialize()
import wmi


######################
# 仪表盘
######################
@login_required
def dashboard(request, funid):
    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')

    return render(request, "dashboard.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages
    })


@login_required
def get_dashboard(request):
    util = request.POST.get('util', '')
    startdate = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d")
    enddate = (datetime.datetime.now()).strftime("%Y-%m-%d")

    clientid = ''
    jobstatus = ''
    try:
        util = int(util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": [],
        })
    # 24小时作业显示成功，执行中，失败状态的个数
    error_job_list = []
    show_job_status_num = ''
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            try:
                dm = SQLApi.CVApi(sqlserver_credit)
                # 24小时作业
                _, show_job_status_num = dm.get_cv_joblist(startdate=startdate,
                                                           enddate=enddate, clientid=clientid, jobstatus=jobstatus)

                # 异常事件
                job_list = dm.display_error_job_list(startdate=startdate, enddate=enddate, clientid=clientid)
                error_job_list = job_list[0:50]
            except Exception as e:
                print(e)
                return JsonResponse({
                    "ret": 0,
                    "data": "获取信息失败。",
                })
    return JsonResponse({"error_job_list": error_job_list,
                         "show_job_status_num": show_job_status_num,
                         })


@login_required
def cv_joblist(request, funid):
    startdate = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d")
    enddate = (datetime.datetime.now()).strftime("%Y-%m-%d")

    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    util = request.GET.get('util', '')
    try:
        util = int(util)
    except:
        pass

    return render(request, "cv_joblist.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages,
        "util_id": util,
        "startdate": startdate,
        "enddate": enddate,
    })


@login_required
def get_cv_joblist(request):
    util = request.GET.get('util', '')
    startdate = request.GET.get('startdate', '')
    enddate = request.GET.get('enddate', '')
    clientid = request.GET.get('clientid', '')
    jobstatus = request.GET.get('jobstatus', '')

    try:
        clientid = int(clientid)
    except:
        clientid = ""

    try:
        util = int(util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": 'Commvault工具未配置。',
        })
    job_list = []
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            try:
                dm = SQLApi.CVApi(sqlserver_credit)
                job_list, _ = dm.get_cv_joblist(startdate, enddate, clientid, jobstatus)

            except Exception as e:
                print(e)
                return JsonResponse({
                    "ret": 0,
                    "data": "获取信息失败。",
                })
    return JsonResponse({"data": job_list})


@login_required
def get_jobbackupsize_daily(request):
    util = request.GET.get('util', '')
    try:
        util = int(util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": 'Commvault工具未配置。',
        })
    job_list = []
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            try:
                dm = SQLApi.CVApi(sqlserver_credit)
                job_list = dm.get_cv_joblist_daily()

            except Exception as e:
                print(e)
                return JsonResponse({
                    "ret": 0,
                    "data": "获取信息失败。",
                })
    return JsonResponse({"data": job_list})



@login_required
def get_jobbytype(request):
    util = request.GET.get('util', '')
    startdate = request.GET.get('startdate', '')
    enddate = request.GET.get('enddate', '')
    clientid = request.GET.get('clientid', '')
    jobstatus = request.GET.get('jobstatus', '')

    try:
        clientid = int(clientid)
    except:
        clientid = ""

    try:
        util = int(util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": 'Commvault工具未配置。',
        })
    job_list = []
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            try:
                dm = SQLApi.CVApi(sqlserver_credit)
                totaljob = dm.get_cv_jobbytype(startdate, enddate, clientid, jobstatus)

            except Exception as e:
                print(e)
                return JsonResponse({
                    "ret": 0,
                    "data": "获取信息失败。",
                })
    return JsonResponse({"data": totaljob})



@login_required
def get_client_name(request):
    utils = request.POST.get('utils', '')

    try:
        utils = int(utils)
        utils_manage = UtilsManage.objects.get(id=utils)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        try:
            dm = SQLApi.CVApi(sqlserver_credit)
            clientname_list = dm.get_clients_name()

        except Exception as e:
            print(e)
            return JsonResponse({
                "ret": 0,
                "data": "获取客户端基础信息失败。",
            })
        else:
            return JsonResponse({
                "ret": 1,
                "data": clientname_list,
            })


@login_required
def display_error_job(request, funid):
    startdate = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d")
    enddate = datetime.datetime.now().strftime("%Y-%m-%d")

    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    util = request.GET.get('util', '')
    try:
        util = int(util)
    except:
        pass
    return render(request, "display_error_job.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages,
        "util_id": util,
        "startdate": startdate,
        "enddate": enddate,
    })


@login_required
def get_display_error_job(request):
    util = request.GET.get('util', '')
    startdate = request.GET.get('startdate', '')
    enddate = request.GET.get('enddate', '')
    clientid = request.GET.get('clientid', '')

    try:
        clientid = int(clientid)
    except:
        clientid = ""

    try:
        util = int(util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": [],
        })
    job_list = []
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            try:
                dm = SQLApi.CVApi(sqlserver_credit)
                job_list = dm.display_error_job_list(startdate=startdate, enddate=enddate, clientid=clientid)

            except Exception as e:
                print(e)
                return JsonResponse({
                    "ret": 0,
                    "data": "获取信息失败。",
                })

    return JsonResponse({"data": job_list})


@login_required
def get_top5_app_capacity(request):
    util = request.POST.get('util', '')
    top5_app_list = []
    try:
        util = int(util)
        utils_manage = UtilsManage.objects.get(id=util)
    except:
        return JsonResponse({
            "ret": 0,
            "data": "Commvault工具未配置。",
        })
    else:
        _, sqlserver_credit = get_credit_info(utils_manage.content)

        try:
            dm = SQLApi.CVApi(sqlserver_credit)
            ret = dm.get_backup_content()
        except:
            pass
        else:
            # 客户端相同的应用程序大小相加
            client_name = ""
            for r in ret:
                if r["clientname"] == client_name:
                    continue
                app_capacity = 0
                client_name = r["clientname"]

                for ir in ret:
                    if client_name == ir["clientname"]:
                        app_capacity += ir["numbytesuncomp"]
                top5_app_list.append({
                    "client_name": client_name,
                    "app_capacity": round(app_capacity / 1024 / 1024 / 1024, 2)
                })

                # str(round(int(pfu[0].AllocatedBaseSize)/1024,2))+'GB'
                client_name = r["clientname"]
    top5_app_list.sort(key=lambda e: e['app_capacity'], reverse=True)
    return JsonResponse({
        "data": str(top5_app_list)
    })


@login_required
def get_frameworkstate(request):
    util = request.POST.get('util', '')
    try:
        util = int(util)
    except:
        raise Http404()
    state = 0
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)
            # 先判断网络
            netresult = ping(commvault_credit["webaddr"])
            if netresult is not None:
                # 网络正常时取接口信息
                cvToken = CV_RestApi_Token()
                commvault_credit["token"] = ""
                commvault_credit["lastlogin"] = 0
                cvToken.login(commvault_credit)
                if not cvToken.isLogin:
                    state = 1
                # 网络正常时取数据库信息
                dm = SQLApi.CVApi(sqlserver_credit)
                if dm.isconnected() is not None:
                    # 数据库正常时取ma信息
                    ma_info = dm.get_ma_info()
                    for ma in ma_info:
                        netresult = ping(ma["InterfaceName"])
                        if netresult is None:
                            state = 1
                    for ma in ma_info:
                        if ma["Offline"] == 0:
                            break
                        else:
                            state = 2
            else:
                state = 2
    return JsonResponse({
        "ret": 1,
        "data": state,
    })


######################
# 灾备基础框架
######################
@login_required
def framework(request, funid):
    util = request.GET.get("util", "")
    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    try:
        util = int(util)
    except:
        pass

    return render(request, "framework.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages,
        "util_id": util,
    })


@login_required
def get_framework(request):
    util = request.POST.get('util', '')
    try:
        util = int(util)
    except:
        raise Http404()
    frameworkdata = {}
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            commserve = {
                'host': '无法获取',
                'version': '无法获取',
                'sp': '无法获取',
                'os': '无法获取',
                'net': '无法获取',

                'apiport': '无法获取',
                'apiconnect': '无法获取',
                'dbname': '无法获取',
                'dbconnect': '无法获取',
            }
            mas = []

            # 先判断网络
            netresult = ping(commvault_credit["webaddr"])
            if netresult is not None:
                commserve["net"] = "正常"
                # 网络正常时取数据库信息
                commserve["dbname"] = sqlserver_credit["SQLServerDataBase"]
                dm = SQLApi.CVApi(sqlserver_credit)
                if dm.isconnected() is not None:
                    commserve["dbconnect"] = "正常"

                    # 数据库连接正常，取cs信息
                    commserv_info = dm.get_commserv_info()
                    if commserv_info is not None:
                        commserve["host"] = commserv_info[3]
                        commserve["version"] = commserv_info[0]
                        commserve["sp"] = commserv_info[1]
                        commserve["os"] = commserv_info[2]
                    # 数据库连接正常，取ma信息
                    ma_info = dm.get_ma_info()
                    for ma in ma_info:
                        netresult = ping(ma["InterfaceName"])
                        if netresult is not None:
                            ma["net"] = "正常"
                        else:
                            ma["net"] = "中断"
                        if ma["Offline"] == 0:
                            ma["Offline"] = "在线"
                        else:
                            ma["Offline"] = "离线"
                        try:
                            ma["TotalSpaceMB"] = round(ma["TotalSpaceMB"] / 1024 / 1024, 2)
                        except:
                            pass
                        try:
                            ma["TotalFreeSpaceMB"] = round(ma["TotalFreeSpaceMB"] / 1024 / 1024, 2)
                        except:
                            pass
                        try:
                            ma["Percent"] = round(
                                (ma["TotalSpaceMB"] - ma["TotalFreeSpaceMB"]) / ma["TotalSpaceMB"] * 100, 2)
                        except:
                            ma["Percent"] = 0
                        try:
                            ma["SpaceReserved"] = round(ma["SpaceReserved"] / 1024 / 1024, 2)
                        except:
                            pass
                        ma["CapacityAvailable"] = ma["TotalFreeSpaceMB"]
                        try:
                            ma["CapacityAvailable"] = ma["TotalFreeSpaceMB"] - ma["SpaceReserved"]
                        except:
                            pass
                        mas.append(ma)
                    frameworkdata["ma"] = mas


                else:
                    commserve["dbconnect"] = "中断"
                commserve["apiport"] = commvault_credit["port"]
                # 网络正常时取接口信息
                cvToken = CV_RestApi_Token()
                commvault_credit["token"] = ""
                commvault_credit["lastlogin"] = 0
                cvToken.login(commvault_credit)
                if cvToken.isLogin:
                    commserve["apiconnect"] = "正常"
                else:
                    commserve["apiconnect"] = "中断"

            else:
                commserve["net"] = "中断"

            frameworkdata["commserve"] = commserve

    return JsonResponse({
        "ret": 1,
        "data": frameworkdata,
    })


@login_required
def get_csinfo(request):
    util = request.POST.get('util', '')
    try:
        util = int(util)
    except:
        raise Http404()
    frameworkdata = {}
    util_manages = UtilsManage.objects.exclude(state='9').filter(id=util)
    if len(util_manages) > 0:
        util = util_manages[0]
        if util.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(util.content)

            commserve = {
                'cpuloadpercentage': '无法获取',
                'memtotal': '无法获取',
                'memutilization': '无法获取',
                'swaptotal': '无法获取',
                'swaputilization': '无法获取',
                'disktotal': '无法获取',
                'diskutilization': '无法获取',
            }
            try:
                conn = wmi.WMI(computer=commvault_credit["webaddr"], user=commvault_credit["hostusername"],
                               password=commvault_credit["hostpasswd"])
                cs = conn.Win32_ComputerSystem()
                ops = conn.Win32_OperatingSystem()
                pfu = conn.Win32_PageFileUsage()
                processor = conn.Win32_Processor()
                dd = conn.Win32_DiskDrive()
                commserve["memtotal"] = str(round(int(cs[0].TotalPhysicalMemory) / 1024 / 1024 / 1024, 2)) + 'GB'
                commserve["memutilization"] = str(round(
                    (int(cs[0].TotalPhysicalMemory) / 1024 - int(ops[0].FreePhysicalMemory)) / (
                                int(cs[0].TotalPhysicalMemory) / 1024) * 100, 2)) + '%'
                commserve["swaptotal"] = str(round(int(pfu[0].AllocatedBaseSize) / 1024, 2)) + 'GB'
                commserve["swaputilization"] = str(round(pfu[0].CurrentUsage / pfu[0].AllocatedBaseSize * 100, 2)) + '%'
                cpuloadpercentage = ""
                for cpu in processor:
                    cpuloadpercentage += str(cpu.DeviceID) + ':' + str(cpu.LoadPercentage) + '% '
                commserve["cpuloadpercentage"] = cpuloadpercentage

                tmplist = []
                diskTotal = 0
                freeSpace = 0
                percent = 0
                for physical_disk in dd:
                    for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                            tmpdict = {}
                            tmpdict["Caption"] = logical_disk.Caption
                            tmpdict["DiskTotal"] = int(logical_disk.Size) / 1024 / 1024 / 1024
                            diskTotal += int(logical_disk.Size) / 1024 / 1024 / 1024
                            tmpdict["FreeSpace"] = int(logical_disk.FreeSpace) / 1024 / 1024 / 1024
                            freeSpace += int(logical_disk.FreeSpace) / 1024 / 1024 / 1024
                            tmpdict["Percent"] = int(
                                100.0 * (int(logical_disk.Size) - int(logical_disk.FreeSpace)) / int(
                                    logical_disk.Size))
                            tmplist.append(tmpdict)
                try:
                    percent = (diskTotal - freeSpace) / diskTotal * 100
                except:
                    pass
                commserve["disktotal"] = str(round(diskTotal, 2)) + 'GB'
                commserve["diskutilization"] = str(round(percent, 2)) + '%'
            except Exception as e:
                pass

            frameworkdata["commserve"] = commserve

    return JsonResponse({
        "ret": 1,
        "data": frameworkdata,
    })


@login_required
def client_list(request, funid):
    util = request.GET.get("util", "")
    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    try:
        util = int(util)
    except:
        pass

    return render(request, "client_list.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages,
        "util_id": util,
    })


@login_required
def sla(request, funid):
    util = request.GET.get("util", "")
    util_manages = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    try:
        util = int(util)
    except:
        pass

    return render(request, "sla.html", {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "util_manages": util_manages,
        "util_id": util,
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
    categories = []

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
        disk_space_weekly_data = DiskSpaceWeeklyData.objects.filter(utils_id=utils_id).filter(media_id=media_id).order_by("extract_time").values()
        capacity_available_list = []
        total_space_list = []

        # 遍历12个月
        if disk_space_weekly_data:
            today = datetime.date.today()
            last_month_capacity_avaible = 0
            last_month_total_space = 0

            for i in range(13):
                c_time = "{0:%Y-%m}".format(today)

                # 当月的表数据 第一条
                has_data = False
                for dswd in disk_space_weekly_data:
                    extract_time = "{0:%Y-%m}".format(dswd["extract_time"]) if dswd["extract_time"] else ""
                    if extract_time == c_time:
                        capacity_available_list.append(round(dswd["capacity_avaible"] / 1024, 2))
                        total_space_list.append(round(dswd["total_space"] / 1024, 2))
                        has_data = True
                        last_month_capacity_avaible = round(dswd["capacity_avaible"] / 1024, 2)
                        last_month_total_space = round(dswd["total_space"] / 1024, 2)
                        break
                
                # 当月未取数
                if i == 0 and not has_data:
                    continue

                if not has_data:
                    # 与上月相同
                    capacity_available_list.append(last_month_capacity_avaible)
                    total_space_list.append(last_month_total_space)

                # 减去一个月
                first_day = today.replace(day=1)
                today = first_day - datetime.timedelta(days=1)

                categories.append(c_time)

            disk_list.append({
                "name": "可用容量",
                "color": "#3598dc",
                "capacity_list": capacity_available_list
            })
            disk_list.append({
                "name": "总容量",
                "color": "#32c5d2",
                "capacity_list": total_space_list
            })
    else:
        # 总
        #   同一次取得的库空间相加
        disk_space_weekly_data = DiskSpaceWeeklyData.objects.filter(utils_id=utils_id).order_by("extract_time").values()
        capacity_available_list = []
        total_space_list = []
        if disk_space_weekly_data:
            today = datetime.date.today()
            last_month_capacity_avaible = 0
            last_month_total_space = 0

            for i in range(13):
                c_time = "{0:%Y-%m}".format(today)

                # 当月的表数据 第一条
                has_data = False
                for dswd in disk_space_weekly_data:
                    extract_time = "{0:%Y-%m}".format(dswd["extract_time"]) if dswd["extract_time"] else ""
                    if extract_time == c_time:  # 当月的
                        # 相同point_tag(第一个)的相加
                        point_tag = dswd["point_tag"]
                        cur_disk_space_weekly_data = [i for i in disk_space_weekly_data if i["utils_id"] == utils_id and i["point_tag"] == point_tag and extract_time == c_time]

                        sum_capacity_avaible = 0
                        sum_total_space = 0
                        for cdswd in cur_disk_space_weekly_data:
                            sum_capacity_avaible += cdswd["capacity_avaible"]
                            sum_total_space += cdswd["total_space"]

                        capacity_available_list.append(round(sum_capacity_avaible / 1024, 2))
                        total_space_list.append(round(sum_total_space / 1024, 2))
                        has_data = True
                        last_month_capacity_avaible = round(sum_capacity_avaible / 1024, 2)
                        last_month_total_space = round(sum_total_space / 1024, 2)
                        break
                # 当月未取数
                if i == 0 and not has_data:
                    continue
                if not has_data:
                    # 与上月相同
                    capacity_available_list.append(last_month_capacity_avaible)
                    total_space_list.append(last_month_total_space)

                # 减去一个月
                first_day = today.replace(day=1)
                today = first_day - datetime.timedelta(days=1)

                categories.append(c_time)

            disk_list.append({
                "name": "可用容量",
                "color": "#3598dc",
                "capacity_list": capacity_available_list
            })
            disk_list.append({
                "name": "总容量",
                "color": "#32c5d2",
                "capacity_list": total_space_list
            })

    return JsonResponse({
        "disk_list": disk_list,
        "categories": categories
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
    utils_id = request.POST.get('util', '')

    # 监控页面url 磁盘空间 url
    funs = Fun.objects.all()
    disk_space = "/"
    client_list = "/"
    for fun in funs:
        if "disk_space" in fun.url:
            disk_space = "{0}?util={1}".format(fun.url, utils_id)
        if "client_list" in fun.url:
            client_list = "{0}?util={1}".format(fun.url, utils_id)
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

            capacity_available_percent = round((capacity_available / total_space) * 100, 2)
            space_reserved_percent = round((space_reserved / total_space) * 100, 2)
            used_space_percent = round((100 - capacity_available_percent - space_reserved_percent), 2)
            data = {
                "capacity_available_percent": capacity_available_percent,
                "space_reserved_percent": space_reserved_percent,
                "used_space_percent": used_space_percent,
                "total_space": round(total_space / 1024 / 1024, 2),
                "used_space": round((total_space - space_reserved - capacity_available) / 1024 / 1024, 2),
                "bk_space_href": disk_space,
                "client_list_href": client_list
            }
        except:
            pass
    return JsonResponse({
        "status": status,
        "info": info,
        "data": data
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
            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_backup_status()

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
            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_backup_content()

            for num, wl in enumerate(whole_list):
                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])
                subclient_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'], subclient=wl['subclient'])
                whole_list[num]['clientname_rowspan'] = clientname_rowspan
                whole_list[num]['idataagent_rowspan'] = idataagent_rowspan
                whole_list[num]['type_rowspan'] = type_rowspan
                whole_list[num]['subclient_rowspan'] = subclient_rowspan

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

            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_storage_policy()

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
            # all_client_manage = Origin.objects.exclude(state="9").values("client_name")
            # tmp_client_manage = [tmp_client["client_name"] for tmp_client in all_client_manage]

            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_schedule_policy()
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
def get_client_info(request):
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
            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_clients_info()
            dm.close()
            for client in whole_list:
                client["net"] = "正常"
                # for i in range(4):
                #     netresult = os.system(u'ping -n 1 ' + client["network_interface"])
                #     if netresult == 0:
                #         client["net"] = "正常"
                #         break;
                # else:
                #     client["net"] = "中断"

        except Exception as e:
            print(e)
            return JsonResponse({
                "ret": 0,
                "data": "获取客户端基础信息失败。",
            })
        else:
            return JsonResponse({
                "ret": 1,
                "data": whole_list,
            })


@login_required
def get_cv_sla(request):
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
            dm = SQLApi.CVApi(sqlserver_credit)
            whole_list = dm.get_sla()

            for num, wl in enumerate(whole_list):
                clientname_rowspan = get_rowspan(whole_list, clientname=wl['clientname'])
                idataagent_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'])
                type_rowspan = get_rowspan(whole_list, clientname=wl['clientname'], idataagent=wl['idataagent'],
                                           type=wl['type'])

                whole_list[num]['clientname_rowspan'] = clientname_rowspan
                whole_list[num]['idataagent_rowspan'] = idataagent_rowspan
                whole_list[num]['type_rowspan'] = type_rowspan

            dm.close()
        except Exception as e:
            return JsonResponse({
                "ret": 0,
                "data": "获取健康度信息失败。",
            })
        return JsonResponse({
            "ret": 1,
            "data": whole_list,
        })
