# 客户端管理
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.db.models import Max
from django.db import transaction


from .tasks import *
from .views import getpagefuns
from faconstor.api import SQLApi
from .public import (
    get_params, get_credit_info
)
import json

import datetime
import pythoncom
from lxml import etree
from concurrent.futures import ThreadPoolExecutor, as_completed
from ast import literal_eval

pythoncom.CoInitialize()
import wmi


######################
# 客户端管理
######################
@login_required
def client_manage(request, funid):
    # 单机恢复预案
    pro_list = []
    pros = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="") | Q(type="NODE")).only("id", "name", "associated_hosts")
    for pro in pros:
        associated_hosts = pro.associated_hosts
        try:
            hosts = etree.XML(associated_hosts).xpath("//host")
            if len(hosts) == 1:  # 单机
                associated_host_list = []
                for h in hosts:
                    associated_host_list.append({
                        "hosts_id": h.attrib.get("id", ""),
                        "hosts_name": h.attrib.get("name", ""),
                    })

                # 流程参数
                process_param_list = get_params(pro.config)

                pro_list.append({
                    "process_id": pro.id,
                    "process_name": pro.name,
                    "hosts": associated_host_list,
                    "process_param_list": process_param_list,
                })
        except Exception as e:
            print(e)

    hosts_manages = HostsManage.objects.exclude(state="9").filter(nodetype='CLIENT').only("id", "host_name", "config")
    hosts_list = []
    for hm in hosts_manages:
        # 主机参数
        host_param_list = get_params(hm.config)
        hosts_list.append({
            "id": hm.id,
            "host_name": hm.host_name,
            "host_param_list": host_param_list
        })

    cv_clients = CvClient.objects.exclude(state="9").values("id", "client_name")
    return render(request, 'client_manage.html', {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "is_superuser": request.user.is_superuser,
        "pro_list": pro_list,
        "pro_list_json": json.dumps(pro_list),
        "hosts_manages": hosts_list,
        "hosts_manages_json": json.dumps(hosts_list),
        'cv_clients': cv_clients,
    })


def get_client_node(parent, select_id, request):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9")
    for child in children:
        # 当前用户所在用户组所拥有的 主机访问权限
        # 如当前用户是管理员 均可访问
        if not request.user.is_superuser and child.nodetype == "CLIENT":
            # 能访问当前主机的所有角色
            # 当前用户所在的所有角色
            # 只要匹配一个就展示
            user_in_groups = request.user.userinfo.group.all()
            host_in_groups = child.group_set.all()

            has_privilege = False

            for uig in user_in_groups:
                for hig in host_in_groups:
                    if uig.id == hig.id:
                        has_privilege = True
                        break
            if not has_privilege:
                continue

        node = dict()
        node["text"] = child.host_name
        node["id"] = child.id
        node["type"] = child.nodetype
        node["data"] = {
            "name": child.host_name,
            "remark": child.remark,
            "pname": parent.host_name
        }

        node["children"] = get_client_node(child, select_id, request)
        if child.id in [1, 2, 3]:
            node["state"] = {"opened": True}
        if child.id == 2:
            node["text"] = "<img src = '/static/pages/images/s.png' height='24px'> " + node["text"]
        if child.id == 3:
            node["text"] = "<img src = '/static/pages/images/d.png' height='24px'> " + node["text"]
        if child.nodetype == "NODE" and child.id not in [1, 2, 3]:
            node[
                "text"] = "<i class='jstree-icon jstree-themeicon fa fa-folder icon-state-warning icon-lg jstree-themeicon-custom'></i>" + \
                          node["text"]
        if child.nodetype == "CLIENT":
            cv_client = CvClient.objects.exclude(state="9").filter(hostsmanage=child)
            if len(cv_client) > 0:
                node["text"] = "<img src = '/static/pages/images/cv.png' height='24px'> " + node["text"]
        try:
            if int(select_id) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def get_client_tree(request):
    select_id = request.POST.get('id', '')
    tree_data = []
    root_nodes = HostsManage.objects.order_by("sort").exclude(state="9").filter(pnode=None).filter(nodetype="NODE")

    for root_node in root_nodes:
        root = dict()
        root["text"] = root_node.host_name
        root["id"] = root_node.id
        root["type"] = root_node.nodetype
        root["data"] = {
            "name": root_node.host_name,
            "remark": root_node.remark,
            "pname": "无"
        }
        if root_node.id == 1:
            root["text"] = "<img src = '/static/pages/images/c.png' height='24px'> " + root["text"]
        try:
            if int(select_id) == root_node.id:
                root["state"] = {"opened": True, "selected": True}
            else:
                root["state"] = {"opened": True}
        except:
            root["state"] = {"opened": True}
        root["children"] = get_client_node(root_node, select_id, request)
        tree_data.append(root)
    return JsonResponse({
        "ret": 1,
        "data": tree_data
    })


@login_required
def clientdel(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            return HttpResponse(0)
        client = HostsManage.objects.get(id=id)
        client.state = "9"
        client.save()

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def client_move(request):
    id = request.POST.get('id', '')
    parent = request.POST.get('parent', '')
    old_parent = request.POST.get('old_parent', '')
    position = request.POST.get('position', '')
    old_position = request.POST.get('old_position', '')
    try:
        id = int(id)  # 节点 id
        parent = int(parent)  # 目标位置父节点 pnode_id
        position = int(position)  # 目标位置
        old_parent = int(old_parent)  # 起点位置父节点 pnode_id
        old_position = int(old_position)  # 起点位置
    except:
        return HttpResponse("0")
    # sort = position + 1 sort从1开始

    # 起始节点下方 所有节点  sort -= 1
    old_client_parent = HostsManage.objects.get(id=old_parent)
    old_sort = old_position + 1
    old_clients = HostsManage.objects.exclude(state="9").filter(pnode=old_client_parent).filter(sort__gt=old_sort)

    # 目标节点下方(包括该节点) 所有节点 sort += 1
    client_parent = HostsManage.objects.get(id=parent)
    sort = position + 1
    clients = HostsManage.objects.exclude(state=9).exclude(id=id).filter(pnode=client_parent).filter(sort__gte=sort)

    my_client = HostsManage.objects.get(id=id)

    # 判断目标父节点是否为接口，若为接口无法挪动
    if client_parent.nodetype == "CLIENT":
        return HttpResponse("客户端")
    else:
        # 目标父节点下所有节点 除了自身 接口名称都不得相同 否则重名
        client_same = HostsManage.objects.exclude(state="9").exclude(id=id).filter(pnode=client_parent).filter(
            host_name=my_client.host_name)

        if client_same:
            return HttpResponse("重名")
        else:
            for old_client in old_clients:
                try:
                    old_client.sort -= 1
                    old_client.save()
                except:
                    pass
            for client in clients:
                try:
                    client.sort += 1
                    client.save()
                except:
                    pass

            # 该节点位置变动
            try:
                my_client.pnode = client_parent
                my_client.sort = sort
                my_client.save()
            except:
                pass

            # 起始 结束 点不在同一节点下 写入父节点名称与ID ?
            if parent != old_parent:
                return HttpResponse(client_parent.host_name + "^" + str(client_parent.id))
            else:
                return HttpResponse("0")


@login_required
def client_node_save(request):
    id = request.POST.get("id", "")
    pid = request.POST.get("pid", "")
    node_name = request.POST.get("node_name", "")
    node_remark = request.POST.get("node_remark", "")

    try:
        id = int(id)
    except:
        ret = 0
        info = "网络错误。"
    else:
        if node_name.strip():
            if id == 0:
                try:
                    cur_host_manage = HostsManage()
                    cur_host_manage.pnode_id = pid
                    cur_host_manage.host_name = node_name
                    cur_host_manage.remark = node_remark
                    cur_host_manage.nodetype = "NODE"
                    # 排序
                    sort = 1
                    try:
                        max_sort = HostsManage.objects.exclude(state="9").filter(pnode_id=pid).aggregate(
                            max_sort=Max('sort', distinct=True))["max_sort"]
                        sort = max_sort + 1
                    except:
                        pass
                    cur_host_manage.sort = sort

                    cur_host_manage.save()
                    id = cur_host_manage.id
                except:
                    ret = 0
                    info = "服务器异常。"
                else:
                    ret = 1
                    info = "新增节点成功。"
            else:
                # 修改
                try:
                    cur_host_manage = HostsManage.objects.get(id=id)
                    cur_host_manage.host_name = node_name
                    cur_host_manage.remark = node_remark
                    cur_host_manage.save()

                    ret = 1
                    info = "节点信息修改成功。"
                except:
                    ret = 0
                    info = "服务器异常。"
        else:
            ret = 0
            info = "节点名称不能为空。"
    return JsonResponse({
        "ret": ret,
        "info": info,
        "nodeid": id
    })


@login_required
def get_cvinfo(request):
    # 工具
    utils_manage = UtilsManage.objects.exclude(state='9').filter(util_type='Commvault')
    data = []

    try:
        pool = ThreadPoolExecutor(max_workers=10)

        all_tasks = [pool.submit(get_instance_list, (um)) for um in utils_manage]
        for future in as_completed(all_tasks):
            if future.result():
                data.append(future.result())
    except:
        pass
    # for um in utils_manage:
    #     data.append(get_instance_list(um))

    # 所有关联终端
    destination = CvClient.objects.exclude(state="9").filter(type__in=['2', '3'])

    u_destination = []

    for um in utils_manage:
        destination_list = []
        for d in destination:
            if d.utils.id == um.id:
                destination_list.append({
                    'id': d.id,
                    'name': d.client_name
                })
        u_destination.append({
            'utilid': um.id,
            'utilname': um.name,
            'destination_list': destination_list
        })
    return JsonResponse({
        "ret": 1,
        "info": "查询成功。",
        "data": data,
        'u_destination': u_destination,
    })


@login_required
def get_client_detail(request):
    hostinfo = {}
    cvinfo = {}
    dbcopyinfo = {}
    kvminfo = {}
    id = request.POST.get("id", "")
    try:
        id = int(id)
        host_manage = HostsManage.objects.get(id=id)

    except:
        ret = 0
        info = "当前客户端不存在。"
    else:
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
        except:
            ret = 0
            info = "数据格式异常，无法获取。"
        else:
            hostinfo = {
                "host_id": host_manage.id,
                "host_ip": host_manage.host_ip,
                "host_name": host_manage.host_name,
                "os": host_manage.os,
                "username": host_manage.username,
                "password": host_manage.password,
                "remark": host_manage.remark,
                "variable_param_list": param_list,
            }
            ret = 1
            info = "查询成功。"

            cc = CvClient.objects.exclude(state="9").filter(hostsmanage_id=id)
            if len(cc) > 0:
                cvinfo["id"] = cc[0].id
                cvinfo["type"] = cc[0].type
                cvinfo["utils_id"] = cc[0].utils_id
                cvinfo["client_id"] = cc[0].client_id
                cvinfo["agentType"] = cc[0].agentType
                cvinfo["instanceName"] = cc[0].instanceName
                cvinfo["destination_id"] = cc[0].destination_id

                # oracle
                cvinfo["copy_priority"] = ""
                cvinfo["db_open"] = ""
                cvinfo["log_restore"] = ""
                cvinfo["data_path"] = ""
                # File System
                cvinfo["overWrite"] = ""
                cvinfo["destPath"] = ""
                cvinfo["sourcePaths"] = ""
                # SQL Server
                cvinfo["mssqlOverWrite"] = ""

                try:
                    config = etree.XML(cc[0].info)
                    param_el = config.xpath("//param")
                    if len(param_el) > 0:
                        cvinfo["copy_priority"] = param_el[0].attrib.get("copy_priority", "")
                        cvinfo["db_open"] = param_el[0].attrib.get("db_open", "")
                        cvinfo["log_restore"] = param_el[0].attrib.get("log_restore", "")
                        cvinfo["data_path"] = param_el[0].attrib.get("data_path", "")

                        cvinfo["overWrite"] = param_el[0].attrib.get("overWrite", "")
                        cvinfo["destPath"] = param_el[0].attrib.get("destPath", "")
                        cvinfo["sourcePaths"] = literal_eval(param_el[0].attrib.get("sourcePaths", "[]"))

                        cvinfo["mssqlOverWrite"] = param_el[0].attrib.get("mssqlOverWrite", "")
                except:
                    pass

            dc = DbCopyClient.objects.exclude(state="9").filter(hostsmanage_id=id)
            if len(dc) > 0:
                dbcopyinfo["id"] = dc[0].id
                dbcopyinfo["hosttype"] = dc[0].hosttype
                dbcopyinfo["dbtype"] = dc[0].dbtype
                if dc[0].dbtype == "1":
                    stdclient = DbCopyClient.objects.exclude(state="9").filter(pri=dc[0])
                    dbcopyinfo["std_id"] = None
                    if len(stdclient) > 0:
                        dbcopyinfo["std_id"] = stdclient[0].id
                    dbcopyinfo["dbusername"] = ""
                    dbcopyinfo["dbpassowrd"] = ""
                    dbcopyinfo["dbinstance"] = ""

                    try:
                        config = etree.XML(dc[0].info)
                        param_el = config.xpath("//param")
                        if len(param_el) > 0:
                            dbcopyinfo["dbusername"] = param_el[0].attrib.get("dbusername", ""),
                            dbcopyinfo["dbpassowrd"] = param_el[0].attrib.get("dbpassowrd", ""),
                            dbcopyinfo["dbinstance"] = param_el[0].attrib.get("dbinstance", ""),
                    except:
                        pass
                if dc[0].dbtype == "2":
                    dbcopyinfo["std_id"] = []
                    stdclientlist = DbCopyClient.objects.exclude(state="9").filter(pri=dc[0])
                    for stdclient in stdclientlist:
                        dbcopyinfo["std_id"].append(str(stdclient.id))
                    dbcopyinfo["dbusername"] = ""
                    dbcopyinfo["dbpassowrd"] = ""
                    dbcopyinfo["copyusername"] = ""
                    dbcopyinfo["copypassowrd"] = ""
                    dbcopyinfo["binlog"] = ""

                    try:
                        config = etree.XML(dc[0].info)
                        param_el = config.xpath("//param")
                        if len(param_el) > 0:
                            dbcopyinfo["dbusername"] = param_el[0].attrib.get("dbusername", ""),
                            dbcopyinfo["dbpassowrd"] = param_el[0].attrib.get("dbpassowrd", ""),
                            dbcopyinfo["copyusername"] = param_el[0].attrib.get("copyusername", ""),
                            dbcopyinfo["copypassowrd"] = param_el[0].attrib.get("copypassowrd", ""),
                            dbcopyinfo["binlog"] = param_el[0].attrib.get("binlog", ""),
                    except:
                        pass

    return JsonResponse({
        "ret": ret,
        "info": info,
        "data": hostinfo,
        "cvinfo": cvinfo,
        "dbcopyinfo": dbcopyinfo,
        "kvminfo": kvminfo
    })


@login_required
def client_client_save(request):
    id = request.POST.get("id", "")
    pid = request.POST.get("pid", "")
    host_ip = request.POST.get("host_ip", "")
    host_name = request.POST.get("host_name", "")
    host_os = request.POST.get("os", "")
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    config = request.POST.get("config", "")
    remark = request.POST.get("remark", "")

    try:
        id = int(id)
    except:
        ret = 0
        info = "网络错误。"
    else:
        if host_ip.strip():
            if host_name.strip():
                if host_os.strip():
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
                            if id == 0:
                                # 判断主机是否已经存在
                                check_host_manage = HostsManage.objects.exclude(state="9").filter(host_name=host_name)
                                if check_host_manage.exists():
                                    ret = 0
                                    info = "主机已经存在，请勿重复添加。"
                                else:
                                    try:
                                        cur_host_manage = HostsManage()
                                        cur_host_manage.pnode_id = pid
                                        cur_host_manage.nodetype = "CLIENT"
                                        cur_host_manage.host_ip = host_ip
                                        cur_host_manage.host_name = host_name
                                        cur_host_manage.os = host_os
                                        cur_host_manage.username = username
                                        cur_host_manage.password = password
                                        cur_host_manage.config = config
                                        cur_host_manage.remark = remark
                                        # 排序
                                        sort = 1
                                        try:
                                            max_sort = \
                                                HostsManage.objects.exclude(state="9").filter(pnode_id=pid).aggregate(
                                                    max_sort=Max('sort', distinct=True))["max_sort"]
                                            sort = max_sort + 1
                                        except:
                                            pass
                                        cur_host_manage.sort = sort

                                        cur_host_manage.save()
                                        id = cur_host_manage.id
                                    except:
                                        ret = 0
                                        info = "服务器异常。"
                                    else:
                                        ret = 1
                                        info = "主机信息新增成功。"
                            else:
                                # 修改
                                try:
                                    cur_host_manage = HostsManage.objects.get(id=id)
                                    cur_host_manage.host_ip = host_ip
                                    cur_host_manage.host_name = host_name
                                    cur_host_manage.os = host_os
                                    cur_host_manage.username = username
                                    cur_host_manage.password = password
                                    cur_host_manage.config = config
                                    cur_host_manage.remark = remark
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
                    info = "系统未选择。"
            else:
                ret = 0
                info = "主机名称不能为空。"
        else:
            ret = 0
            info = "主机IP未填写。"
    return JsonResponse({
        "ret": ret,
        "info": info,
        "nodeid": id
    })


@login_required
def client_cv_save(request):
    id = request.POST.get("id", "")
    cv_id = request.POST.get("cv_id", "")
    cvclient_type = request.POST.get("cvclient_type", "")
    cvclient_utils_manage = request.POST.get("cvclient_utils_manage", "")
    cvclient_source = request.POST.get("cvclient_source", "")
    cvclient_clientname = request.POST.get("cvclient_clientname", "")
    cvclient_agentType = request.POST.get("cvclient_agentType", "")
    cvclient_instance = request.POST.get("cvclient_instance", "")
    cvclient_destination = request.POST.get("cvclient_destination", "")

    # oracle
    cvclient_copy_priority = request.POST.get("cvclient_copy_priority", "")
    cvclient_db_open = request.POST.get("cvclient_db_open", "")
    cvclient_log_restore = request.POST.get("cvclient_log_restore", "")
    cvclient_data_path = request.POST.get("cvclient_data_path", "")

    # File System
    cv_mypath = request.POST.get("cv_mypath", "")
    cv_iscover = request.POST.get("cv_iscover", "")
    cv_selectedfile = request.POST.get("cv_selectedfile", "")

    # SQL Server
    mssql_iscover = request.POST.get("mssql_iscover", "")

    try:
        id = int(id)
        cv_id = int(cv_id)
        cvclient_utils_manage = int(cvclient_utils_manage)
    except:
        ret = 0
        info = "网络错误。"
    else:
        if cvclient_type.strip():
            if cvclient_source.strip():
                if cvclient_agentType.strip():
                    cv_params = {}
                    if "Oracle" in cvclient_agentType:
                        cv_params = {
                            "copy_priority": cvclient_copy_priority,
                            "db_open": cvclient_db_open,
                            "log_restore": cvclient_log_restore,
                            "data_path": cvclient_data_path,
                        }
                    elif "File System" in cvclient_agentType:
                        inPlace = True
                        if cv_mypath != "same":
                            inPlace = False
                        overWrite = False
                        if cv_iscover == "TRUE":
                            overWrite = True

                        sourceItemlist = cv_selectedfile.split("*!-!*")
                        for sourceItem in sourceItemlist:
                            if sourceItem == "":
                                sourceItemlist.remove(sourceItem)
                        cv_params = {
                            "overWrite": overWrite,
                            "inPlace": inPlace,
                            "destPath": cv_mypath,
                            "sourcePaths": sourceItemlist,
                            "OSRestore": False
                        }
                    elif "SQL Server" in cvclient_agentType:
                        mssqlOverWrite = False
                        if mssql_iscover == "TRUE":
                            mssqlOverWrite = True
                        cv_params = {
                            "mssqlOverWrite": mssqlOverWrite,
                        }
                    # 新增
                    if cv_id == 0:
                        try:
                            cvclient = CvClient()
                            cvclient.hostsmanage_id = id
                            cvclient.utils_id = cvclient_utils_manage
                            cvclient.client_id = cvclient_source
                            cvclient.client_name = cvclient_clientname
                            cvclient.type = cvclient_type
                            cvclient.agentType = cvclient_agentType
                            cvclient.instanceName = cvclient_instance
                            if cvclient_type in ("1", "3"):
                                config = custom_cv_params(**cv_params)
                                cvclient.info = config
                                if cvclient_destination != "self":
                                    try:
                                        cvclient_destination = int(cvclient_destination)
                                        cvclient.destination_id = cvclient_destination
                                    except:
                                        pass
                            cvclient.save()
                            if cvclient_destination == "self":
                                cvclient.destination_id = cvclient.id
                                cvclient.save()
                            cv_id = cvclient.id
                        except:
                            ret = 0
                            info = "服务器异常。"
                        else:
                            ret = 1
                            info = "Commvault保护创建成功。"
                    else:
                        # 修改
                        try:
                            cvclient = CvClient.objects.get(id=cv_id)
                            cvclient.hostsmanage_id = id
                            cvclient.utils_id = cvclient_utils_manage
                            cvclient.client_id = cvclient_source
                            cvclient.client_name = cvclient_clientname
                            cvclient.type = cvclient_type
                            cvclient.agentType = cvclient_agentType
                            cvclient.instanceName = cvclient_instance
                            if cvclient_type in ("1", "3"):
                                config = custom_cv_params(**cv_params)
                                cvclient.info = config
                                if cvclient_destination == "self":
                                    cvclient.destination_id = cv_id
                                else:
                                    try:
                                        cvclient_destination = int(cvclient_destination)
                                        cvclient.destination_id = cvclient_destination
                                    except Exception as e:
                                        pass
                            cvclient.save()
                            ret = 1
                            info = "Commvault保护修改成功。"
                        except Exception as e:
                            ret = 0
                            info = "服务器异常。"
                else:
                    ret = 0
                    info = "应用类型不能为空。"
            else:
                ret = 0
                info = "源客户端不能为空。"
        else:
            ret = 0
            info = "客户端类型不能为空。"
    return JsonResponse({
        "ret": ret,
        "info": info,
        "cv_id": cv_id
    })


@login_required
def client_cv_del(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            return HttpResponse(0)
        cv = CvClient.objects.get(id=id)
        cv.state = "9"
        cv.save()

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def client_cv_get_backup_his(request):
    id = request.GET.get('id', '')

    result = []
    try:
        id = int(id)
        cvclient = CvClient.objects.get(id=id)
        utils_manage = cvclient.utils
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        dm = SQLApi.CVApi(sqlserver_credit)
        result = dm.get_all_backup_job_list(cvclient.client_name, cvclient.agentType, cvclient.instanceName)
        dm.close()
    except Exception as e:
        print(e)

    return JsonResponse({"data": result})


@login_required
def client_cv_recovery(request):
    if request.method == 'POST':
        cv_id = request.POST.get('cv_id', '')
        sourceClient = request.POST.get('sourceClient', '')
        destClient = request.POST.get('destClient', '')
        restoreTime = request.POST.get('restoreTime', '')
        browseJobId = request.POST.get('browseJobId', '')
        agent = request.POST.get('agent', '')

        #################################
        # sourceClient>> instance_name  #
        #################################
        instance = ""
        try:
            pri = CvClient.objects.exclude(state="9").get(id=int(cv_id))
        except CvClient.DoesNotExist as e:
            return HttpResponse("恢复任务启动失败, 源客户端不存在。")
        else:
            instance = pri.instanceName
            if not instance:
                return HttpResponse("恢复任务启动失败, 实例不存在。")

            # 账户信息
            utils_content = pri.utils.content if pri.utils else ""
            commvault_credit, sqlserver_credit = get_credit_info(utils_content)

            # 区分应用
            if "Oracle" in agent:
                data_path = request.POST.get('data_path', '')
                copy_priority = request.POST.get('copy_priority', '')
                data_sp = request.POST.get('data_sp', '')

                try:
                    copy_priority = int(copy_priority)
                except:
                    pass
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
                oraRestoreOperator = {"curSCN": curSCN, "browseJobId": None, "data_path": data_path,
                                      "copy_priority": copy_priority, "restoreTime": restoreTime}

                cvToken = CV_RestApi_Token()
                cvToken.login(commvault_credit)
                cvAPI = CV_API(cvToken)
                if agent == "Oracle Database":
                    if cvAPI.restoreOracleBackupset(sourceClient, destClient, instance, oraRestoreOperator):
                        return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
                    else:
                        return HttpResponse("恢复任务启动失败。" + cvAPI.msg)
                elif agent.upper() == "Oracle RAC":
                    oraRestoreOperator["browseJobId"] = browseJobId
                    if cvAPI.restoreOracleRacBackupset(sourceClient, destClient, instance, oraRestoreOperator):
                        return HttpResponse("恢复任务已经启动。" + cvAPI.msg)
                    else:
                        return HttpResponse("恢复任务启动失败。" + cvAPI.msg)
                else:
                    return HttpResponse("无当前模块，恢复任务启动失败。")
            elif "File System" in agent:
                iscover = request.POST.get('iscover', '')
                mypath = request.POST.get('mypath', '')
                selectedfile = request.POST.get('selectedfile')
                sourceItemlist = selectedfile.split("*!-!*")
                inPlace = True
                if mypath != "same":
                    inPlace = False
                overWrite = False
                if iscover == "TRUE":
                    overWrite = True

                for sourceItem in sourceItemlist:
                    if sourceItem == "":
                        sourceItemlist.remove(sourceItem)

                fileRestoreOperator = {"restoreTime": restoreTime, "overWrite": overWrite, "inPlace": inPlace,
                                       "destPath": mypath, "sourcePaths": sourceItemlist, "OS Restore": False}

                cvToken = CV_RestApi_Token()
                cvToken.login(commvault_credit)
                cvAPI = CV_API(cvToken)
                if cvAPI.restoreFSBackupset(sourceClient, destClient, "defaultBackupSet", fileRestoreOperator):
                    return HttpResponse("恢复任务已经启动。")
                else:
                    return HttpResponse("恢复任务启动失败。")
            elif "SQL Server" in agent:
                mssql_iscover = request.POST.get('mssql_iscover', '')
                mssqlOverWrite = False
                if mssql_iscover == "TRUE":
                    mssqlOverWrite = True
                cvToken = CV_RestApi_Token()
                cvToken.login(commvault_credit)
                cvAPI = CV_API(cvToken)
                mssql_dbs = cvAPI.get_mssql_db(pri.client_id, instance)
                mssqlRestoreOperator = {"restoreTime": restoreTime, "overWrite": mssqlOverWrite, "mssql_dbs": mssql_dbs}
                if cvAPI.restoreMssqlBackupset(sourceClient, destClient, instance, mssqlRestoreOperator):
                    return HttpResponse("恢复任务已经启动。")
                else:
                    return HttpResponse(u"恢复任务启动失败。")
    else:
        return HttpResponse("恢复任务启动失败。")


@login_required
def client_cv_get_restore_his(request):
    id = request.GET.get('id', '')

    result = []
    try:
        id = int(id)
        cvclient = CvClient.objects.get(id=id)
        utils_manage = cvclient.utils
        _, sqlserver_credit = get_credit_info(utils_manage.content)
        dm = SQLApi.CVApi(sqlserver_credit)
        result = dm.get_all_restore_job_list(cvclient.client_name, cvclient.agentType, cvclient.instanceName)
        dm.close()
    except Exception as e:
        print(e)
    return JsonResponse({"data": result})


@login_required
def get_cv_process(request):
    id = request.POST.get('id', "")
    try:
        id = int(id)
    except:
        id = 0

    cv_process_list = []
    if id != 0:
        # 所属流程
        processlist = Process.objects.filter(hosts_id=id, type='Commvault', processtype="1").exclude(state="9")
        for process in processlist:
            cv_process_list.append({
                "process_id": process.id,
                "process_name": process.name
            })

    return JsonResponse({
        "ret": 1,
        "process": cv_process_list
    })


@login_required
def get_file_tree(request):
    id = request.POST.get('id', '')
    cv_id = request.POST.get('cv_id', '')
    treedata = []

    try:
        cv_id = int(cv_id)
        pri = CvClient.objects.exclude(state="9").get(id=int(cv_id))
    except Exception:
        pass
    else:
        client_id = pri.client_id
        utils_content = pri.utils.content if pri.utils else ""
        commvault_credit, _ = get_credit_info(utils_content)
        cvToken = CV_RestApi_Token()
        cvToken.login(commvault_credit)
        cvAPI = CV_API(cvToken)
        file_list = []
        try:
            file_list = cvAPI.browse(client_id, "File System", None, id, False)
            for node in file_list:
                root = {}
                root["id"] = node["path"]
                root["pId"] = id
                root["name"] = node["path"]
                if node["DorF"] == "D":
                    root["isParent"] = True
                else:
                    root["isParent"] = False
                treedata.append(root)
        except Exception:
            pass
        treedata = json.dumps(treedata)

    return HttpResponse(treedata)


@login_required
def pro_save(request):
    """
    config:
        <root>
            <process>
                <param param_name variable_name param_value></param>
                <param param_name variable_name param_value></param>
            </process>
            <host hosts_id host_uuid host_given_name host_name>
                <param param_name variable_name param_value></param>
                <param param_name variable_name param_value></param>
            </host>
        </root>
    :param request:
    :return:
    """
    status = 1
    info = "保存成功。"

    p_id = request.POST.get("p_id", "")
    pros_id = request.POST.get("pros_id", "")
    pro_ins = request.POST.get("pro_ins", "")
    config = request.POST.get("config", "{}")
    config_xml = "</root>"
    # JSON TO XML
    try:
        root = etree.Element("root")

        config = json.loads(config)

        process_config = config["PROCESS"]
        hosts_config = config["HOSTS"]

        process_node = etree.SubElement(root, "process")
        for p in process_config:
            params = p["params"]
            for param in params:
                params_node = etree.SubElement(process_node, "param")
                params_node.attrib["param_name"] = param["param_name"]
                params_node.attrib["variable_name"] = param["variable_name"]
                params_node.attrib["param_value"] = param["param_value"]

        for h in hosts_config:
            host_node = etree.SubElement(root, "host")
            host_node.attrib["host_id"] = h["host_id"]
            host_node.attrib["host_uuid"] = h["host_uuid"]
            host_node.attrib["host_given_name"] = h["host_given_name"]
            host_node.attrib["host_name"] = h["host_name"]
            params = h["params"]
            for param in params:
                params_node = etree.SubElement(host_node, "param")
                params_node.attrib["param_name"] = param["param_name"]
                params_node.attrib["variable_name"] = param["variable_name"]
                params_node.attrib["param_value"] = param["param_value"]
        config_xml = etree.tounicode(root)
    except:
        pass

    try:
        p_id = int(p_id)
    except ValueError as e:
        status = 0
        info = "保存失败。"
    else:
        if not pro_ins:
            status = 0
            info = "流程实例名称未填写。"
        else:
            try:
                pros_id = int(pros_id)
            except:
                status = 0
                info = "预案未选择。"
            else:
                # 创建排错流程实例
                def set_troubleshoot_pro_ins(process_id, p_id):
                    """
                    @process_id{int}: 主流程ID
                    @p_id{int}: 主流程实例ID
                    return troubleshoot_pro_ins_list{list}
                    """
                    troubleshoot_pro_ins_list = []
                    try:
                        pros = Process.objects.get(id=process_id)
                    except:
                        raise Exception('PROCESS DOES NOT EXIST')
                    else:
                        troubleshoot_pros = pros.children.exclude(state='9')
                        for troubleshoot_pro in troubleshoot_pros:
                            troubleshoot_pro_ins_id = ProcessInstance.objects.create(**{
                                "name": '{0}的排错流程'.format(pro_ins),
                                "process_id": troubleshoot_pro.id,
                                "pnode_id": p_id,
                            }).id
                            troubleshoot_pro_ins_list.append(troubleshoot_pro_ins_id)
                    return troubleshoot_pro_ins_list
                if p_id == 0:
                    try:
                        with transaction.atomic():
                            p_id = ProcessInstance.objects.create(**{
                                "name": pro_ins,
                                "process_id": pros_id,
                                "config": config_xml,
                            }).id
                            set_troubleshoot_pro_ins(pros_id, p_id)
                    except:
                        status = 0
                        info = "新增失败。"
                else:
                    try:
                        ProcessInstance.objects.filter(id=p_id).update(**{
                            "name": pro_ins,
                            "process_id": pros_id,
                            "config": config_xml,
                        })
                    except:
                        status = 0
                        info = "修改失败。"

    return JsonResponse({
        "status": status,
        "info": info,
        "data": p_id,
    })


@login_required
def get_pro_data(request):
    """
    associated_hosts_xml:
        <root>
            <host hosts_id host_uuid host_given_name host_name></host>
        </root>
    config_xml:
        <root>
            <process>
                <param param_name variable_name param_value></param>
                <param param_name variable_name param_value></param>
            </process>
            <host hosts_id host_uuid host_given_name host_name>
                <param param_name variable_name param_value></param>
                <param param_name variable_name param_value></param>
            </host>
        </root>
    :param request:
    :return: id name process_name associated_name

    """
    result = []
    h_id = request.GET.get("host_id", "")  # 若为单机 仅有一台 且ID相同
    empty = request.GET.get("empty", "false")

    if empty == "false":
        p_inss = ProcessInstance.objects.exclude(state="9").filter(pnode=None)
        for p_ins in p_inss:
            # 判断host_id是否相同，且仅有一台
            is_same_host = False
            is_single_host = False

            config = {}
            associated_name = ""

            try:
                config_root = etree.XML(p_ins.config)
                # 流程参数
                process_nodes = config_root.xpath("//process")
                process_params = []
                if process_nodes:
                    p_param_nodes = process_nodes[0].xpath("./param")
                    for p_param_node in p_param_nodes:
                        process_params.append({
                            "param_name": p_param_node.attrib.get("param_name", ""),
                            "variable_name": p_param_node.attrib.get("variable_name", ""),
                            "param_value": p_param_node.attrib.get("param_value", ""),
                        })

                config["PROCESS"] = [{
                    "params": process_params,
                }]
                # 主机参数
                host_root = etree.XML(p_ins.config)
                host_nodes = host_root.xpath("//host")
                host_list = []

                if len(host_nodes) == 1:
                    is_single_host = True

                for host_node in host_nodes:
                    host_id = host_node.attrib.get("host_id", "")
                    host_uuid = host_node.attrib.get("host_uuid", "")
                    host_given_name = host_node.attrib.get("host_given_name", "")
                    host_name = host_node.attrib.get("host_name", "")

                    host_params = []
                    host_param_nodes = host_node.xpath("./param")
                    for h_param_node in host_param_nodes:
                        host_params.append({
                            "param_name": h_param_node.attrib.get("param_name", ""),
                            "variable_name": h_param_node.attrib.get("variable_name", ""),
                            "param_value": h_param_node.attrib.get("param_value", ""),
                        })
                    host_list.append({
                        "host_id": host_id,
                        "host_uuid": host_uuid,
                        "host_given_name": host_given_name,
                        "host_name": host_name,
                        "params": host_params
                    })
                    associated_name += "{0}, ".format(host_name)

                    if host_id == h_id and h_id:
                        is_same_host = True
                        break
                config["HOST"] = host_list
            except:
                pass

            if all([is_same_host, is_single_host]) or not h_id:
                result.append({
                    "config": config,
                    "id": p_ins.id,
                    "name": p_ins.name,
                    "process_id": p_ins.process_id,
                    "process_name": p_ins.process.name if p_ins.process else "",
                    "associated_name": associated_name if not associated_name.endswith(", ") else associated_name[:-2],
                })

    return JsonResponse({
        "data": result,
    })


@login_required
def pro_del(request):
    status = 1
    info = '删除成功。'
    pro_ins_id = request.POST.get('pro_ins_id', '')

    try:
        pro_ins_id = int(pro_ins_id)
    except:
        status = 0
        info = '网络异常。'
    else:
        pro_ins = ProcessInstance.objects.filter(id=pro_ins_id)
        if pro_ins.exists():
            pro_ins.update(**{'state': '9'})
        else:
            status = 0
            info = '该流程实例不存在，删除失败。'
    return JsonResponse({
        'status': status,
        'info': info
    })


@login_required
def processinsconfig(request, funid):
    # 单机恢复预案
    pro_list = []
    pros = Process.objects.exclude(state="9").exclude(
        Q(type=None) | Q(type="") | Q(type="NODE")
    ).only("id", "name", "associated_hosts")
    for pro in pros:
        associated_hosts = pro.associated_hosts
        try:
            hosts = etree.XML(associated_hosts).xpath("//host")
            associated_host_list = []
            for h in hosts:
                associated_host_list.append({
                    "hosts_id": h.attrib.get("id", ""),
                    "hosts_name": h.attrib.get("name", ""),
                })

            # 流程参数
            process_param_list = get_params(pro.config)

            pro_list.append({
                "process_id": pro.id,
                "process_name": pro.name,
                "hosts": associated_host_list,
                "process_param_list": process_param_list,
            })
        except Exception as e:
            print(e)

    hosts_manages = HostsManage.objects.exclude(state="9").filter(nodetype='CLIENT').only(
        "id", "host_name", "config"
    )
    hosts_list = []
    for hm in hosts_manages:
        # 主机参数
        host_param_list = get_params(hm.config)
        hosts_list.append({
            "id": hm.id,
            "host_name": hm.host_name,
            "host_param_list": host_param_list
        })

    cv_clients = CvClient.objects.exclude(state="9").values("id", "client_name")
    return render(request, 'processinsconfig.html', {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "is_superuser": request.user.is_superuser,
        "pro_list": pro_list,
        "pro_list_json": json.dumps(pro_list),
        "hosts_manages": hosts_list,
        "hosts_manages_json": json.dumps(hosts_list),
        'cv_clients': cv_clients,
    })


@login_required
def get_cv_params(request):
    pro_ins_id = request.POST.get('pro_ins_id', '')

    is_commvault = 0
    agent_type = ''
    cv_params = {
        "pri_id": "",
        "pri_name": "",
        "std_id": "",
        # Oracle
        "data_path": "",
        "copy_priority": "",
        "db_open": "",
        "log_restore": "",
        # File System
        "destPath": "",
        "overWrite": "",
        "inPlace": "",
        "OSRestore": "",
        "sourcePaths": "",
        # SQL Server
        "mssqlOverWrite": "",
    }
    try:
        pro_ins_id = int(pro_ins_id)
        pro_ins = ProcessInstance.objects.get(id=pro_ins_id)
        config_root = etree.XML(pro_ins.config)
        # HOST -> CVCLIENT -> CV_PARAMS
        hosts = config_root.xpath('//host')
        for host in hosts:
            host_id = host.attrib.get('host_id', '')
            try:
                host_id = int(host_id)
            except:
                pass
            cv_clients = CvClient.objects.exclude(state='9').filter(hostsmanage_id=host_id)
            if cv_clients.exists():
                is_commvault = 1
                pri = cv_clients[0]
                agent_type = pri.agentType
                std_id = pri.destination.id if pri.destination else ""
                cv_params["pri_id"] = pri.id
                cv_params["pri_name"] = pri.client_name
                cv_params["std_id"] = std_id

                info = etree.XML(pri.info)
                params = info.xpath("//param")

                if params:
                    param = params[0]

                    # 恢复时间点
                    cv_params["recovery_time"] = param.attrib.get("recovery_time", "")

                    # Oracle
                    cv_params["data_path"] = param.attrib.get("data_path", "")
                    cv_params["copy_priority"] = param.attrib.get("copy_priority", "")
                    cv_params["db_open"] = param.attrib.get("db_open", "")
                    cv_params["log_restore"] = param.attrib.get("log_restore", "")
                    # File System
                    cv_params["destPath"] = param.attrib.get("destPath", "")
                    cv_params["overWrite"] = param.attrib.get("overWrite", "")
                    cv_params["inPlace"] = param.attrib.get("inPlace", "")
                    cv_params["OSRestore"] = param.attrib.get("OSRestore", "")
                    cv_params["sourcePaths"] = literal_eval(param.attrib.get("sourcePaths", "[]"))

                    # SQL Server
                    cv_params["mssqlOverWrite"] = param.attrib.get("mssqlOverWrite", "")
    except:
        pass
    
    return JsonResponse({
        'data': {
            'cv_params': cv_params,
            'agent_type': agent_type,
            'is_commvault': is_commvault,
        },
    })


def get_instance_list(um):
    # 解析出账户信息
    _, sqlserver_credit = get_credit_info(um.content)

    #############################################
    # clientid, clientname, agent, instance, os #
    #############################################
    dm = SQLApi.CVApi(sqlserver_credit)

    instance_data = dm.get_all_instance()

    dm.close()
    instance_list = []
    for od in instance_data:
        instance_list.append({
            "clientid": od["clientid"],
            "clientname": od["clientname"],
            "agent": od["agent"],
            "instance": od["instance"],
        })
    return {
        'utils_manage': um.id,
        'instance_list': instance_list
    }


def custom_cv_params(**kwargs):
    """构造参数xml
    """
    root = etree.Element("root")
    param_node = etree.SubElement(root, "param")
    for k, v in kwargs.items():
        param_node.attrib['{0}'.format(k)] = str(v)
    config = etree.tounicode(root)
    return config
