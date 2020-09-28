# 流程配置：场景配置、流程配置、流程计划、工具管理、接口管理
from django.db import reset_queries
from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from ast import literal_eval

from django.contrib.auth.decorators import login_required
from faconstor.models import *
import json
from lxml import etree
from .views import getpagefuns,get_credit_info,get_params,get_variable_name
from django.db.models import Q
from django.db.models import Max
import copy
import datetime
import base64
from djcelery.models import CrontabSchedule, PeriodicTask
import uuid

@login_required
def script_save(request):
    status = 1
    info = "保存成功。"
    select_id = ""

    id = request.POST.get('id', '')
    code = request.POST.get('code', '')
    name = request.POST.get('name', '')

    # script_text
    script_text = request.POST.get('script_text', '')

    success_text = request.POST.get('success_text', '')
    log_address = request.POST.get('log_address', '')

    # commvault接口
    interface_type = request.POST.get('interface_type', '')

    # 类名
    commv_interface = request.POST.get('commv_interface', '')

    pid = request.POST.get('pid', '')
    my_type = request.POST.get('my_type', '')
    remark = request.POST.get('remark', '')
    pname = request.POST.get('pname')

    # 节点
    node_remark = request.POST.get('node_remark', '')
    node_pname = request.POST.get('node_pname', '')
    node_name = request.POST.get('node_name', '')

    insert_params = request.POST.get('insert_params', '')
    try:
        insert_params = json.loads(insert_params)
    except Exception as e:
        pass

    # 节点存储方法
    def node_save(save_data):
        status = 1
        info = "保存成功。"
        # 删除ID
        copy_save_data = copy.deepcopy(save_data)
        copy_save_data.pop("id")
        if save_data["id"] == 0:
            select_id = save_data["pnode_id"]
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
                status = 1
                select_id = scriptsave.id
            except Exception as e:
                print(e)
                status = 0
                info = "新增接口失败。"
        else:
            # 修改
            select_id = save_data["id"]
            try:
                Script.objects.filter(id=save_data["id"]).update(**copy_save_data)
                status = 1
            except:
                status = 0
                info = "修改接口失败。"
        return status, info, select_id

    # 接口存储方法
    def interface_save(save_data):
        status = 1
        info = "保存成功。"

        if save_data["id"] == 0:
            select_id = save_data["pnode_id"]
            allscript = Script.objects.filter(code=save_data["code"]).exclude(state="9")
            if allscript.exists():
                status = 0
                info = '脚本编码:' + save_data["code"] + '已存在。'
            else:
                scriptsave = Script()
                scriptsave.code = save_data["code"]
                scriptsave.name = save_data["name"]
                scriptsave.type = save_data["type"]
                scriptsave.pnode_id = save_data["pnode_id"]
                scriptsave.remark = save_data["remark"]
                scriptsave.config = save_data["config"]

                # 判断是否commvault/脚本
                if save_data["interface_type"] == "Commvault":
                    scriptsave.script_text = ""
                    scriptsave.succeedtext = ""
                    scriptsave.commv_interface = save_data["commv_interface"]
                else:
                    scriptsave.script_text = save_data["script_text"]
                    scriptsave.succeedtext = save_data["succeedtext"]
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
                select_id = scriptsave.id
                status = 1
        else:
            # 修改
            select_id = id
            allscript = Script.objects.exclude(id=save_data["id"]).filter(code=save_data["code"]).exclude(state="9")
            if allscript.exists():
                info = '脚本编码:' + save_data["code"] + '已存在。'
                status = 0
            else:
                try:
                    scriptsave = Script.objects.get(id=save_data["id"])
                    scriptsave.code = save_data["code"]
                    scriptsave.name = save_data["name"]
                    scriptsave.type = save_data["type"]
                    scriptsave.remark = save_data["remark"]
                    scriptsave.config = save_data["config"]

                    # 判断是否commvault/脚本
                    if save_data["interface_type"] == "Commvault":
                        scriptsave.hosts_manage_id = None
                        scriptsave.script_text = ""
                        scriptsave.succeedtext = ""
                        scriptsave.commv_interface = save_data["commv_interface"]
                    else:
                        scriptsave.script_text = save_data["script_text"]
                        scriptsave.succeedtext = save_data["succeedtext"]
                        scriptsave.commv_interface = ""

                    scriptsave.interface_type = save_data["interface_type"]

                    scriptsave.save()
                    status = 1
                except Exception as e:
                    print("scriptsave edit error:%s" % e)
                    status = 0
                    info = "修改失败。"

        return status, info, select_id

    try:
        id = int(id)
        pid = int(pid)
    except ValueError as e:
        status = 0
        info = "网络连接异常。"
    else:
        status = ""
        # NODE/INTERFACE
        if my_type == "NODE":
            save_data = {
                "id": id,
                "code": "",
                "name": node_name,
                "script_text": "",
                "succeedtext": "",
                "interface_type": "",
                "remark": node_remark,
                "pnode_id": pid,
                "type": my_type,
            }
            status, info, select_id = node_save(save_data)
        else:
            # 脚本参数
            root = etree.Element("root")

            if insert_params:
                # 动态参数
                for insert_param in insert_params:
                    param_node = etree.SubElement(root, "param")
                    param_node.attrib["param_name"] = insert_param["param_name"].strip()
                    param_node.attrib["variable_name"] = insert_param["variable_name"].strip()
                    param_node.attrib["param_value"] = insert_param["param_value"].strip()
            config = etree.tounicode(root)

            save_data = {
                "id": id,
                "code": code,
                "name": name,
                "script_text": script_text,
                "succeedtext": success_text,
                "interface_type": interface_type,
                "commv_interface": commv_interface,
                "remark": remark,
                "pnode_id": pid,
                "type": my_type,
                "config": config,
            }
            if code.strip() == '':
                info = '接口编码不能为空。'
                status = 0
            else:
                if name.strip() == '':
                    info = '接口名称不能为空。'
                    status = 0
                else:
                    # 区分interface_type: commvault/脚本
                    if interface_type.strip() == "":
                        info = '接口类型未选择。'
                        status = 0
                    else:
                        if interface_type == "Commvault":
                            if not commv_interface:
                                info = 'Commvault类名不能为空。'
                                status = 0
                            else:
                                status, info, select_id = interface_save(save_data)
                        else:
                            if script_text.strip() == '':
                                info = '脚本内容不能为空。'
                                status = 0
                            else:
                                status, info, select_id = interface_save(save_data)
    return JsonResponse({
        "status": status,
        "info": info,
        "data": select_id
    })


@login_required
def get_script_detail(request):
    status = 1
    info = ""
    data = {}
    selected_id = request.POST.get("id", "")

    try:
        cur_script = Script.objects.get(id=int(selected_id))
    except Exception as e:
        status = 0
        info = "获取脚本信息失败。"
    else:
        # 脚本参数
        param_list = []
        try:
            config = etree.XML(cur_script.config)

            param_el = config.xpath("//param")
            for v_param in param_el:
                param_list.append({
                    "param_name": v_param.attrib.get("param_name", ""),
                    "variable_name": v_param.attrib.get("variable_name", ""),
                    "param_value": v_param.attrib.get("param_value", ""),
                })
        except Exception as e:
            print(e)

        data = {
            "pname": cur_script.pnode.name if cur_script.pnode else "",
            "remark": cur_script.remark,
            "code": cur_script.code,
            "name": cur_script.name,
            "type": cur_script.type,
            "interface_type": cur_script.interface_type,
            "commv_interface": cur_script.commv_interface,
            "script_text": cur_script.script_text,
            "success_text": cur_script.succeedtext,
            "variable_param_list": param_list,
        }
    return JsonResponse({
        "status": status,
        "info": info,
        "data": data
    })


@login_required
def scriptdel(request):
    """
    当删除脚本管理中的脚本的同时
    :param request:
    :return:
    """
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            return HttpResponse(0)
        script = Script.objects.get(id=id)
        script.state = "9"
        script.save()

        return HttpResponse(1)
    else:
        return HttpResponse(0)


@login_required
def script_move(request):
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
    old_script_parent = Script.objects.get(id=old_parent)
    old_sort = old_position + 1
    old_scripts = Script.objects.exclude(state="9").filter(pnode=old_script_parent).filter(sort__gt=old_sort)

    # 目标节点下方(包括该节点) 所有节点 sort += 1
    script_parent = Script.objects.get(id=parent)
    sort = position + 1
    scripts = Script.objects.exclude(state=9).exclude(id=id).filter(pnode=script_parent).filter(sort__gte=sort)

    my_script = Script.objects.get(id=id)

    # 判断目标父节点是否为接口，若为接口无法挪动
    if script_parent.type == "INTERFACE":
        return HttpResponse("接口")
    else:
        # 目标父节点下所有节点 除了自身 接口名称都不得相同 否则重名
        script_same = Script.objects.exclude(state="9").exclude(id=id).filter(pnode=script_parent).filter(
            name=my_script.name)

        if script_same:
            return HttpResponse("重名")
        else:
            for old_script in old_scripts:
                try:
                    old_script.sort -= 1
                    old_script.save()
                except:
                    pass
            for script in scripts:
                try:
                    script.sort += 1
                    script.save()
                except:
                    pass

            # 该节点位置变动
            try:
                my_script.pnode = script_parent
                my_script.sort = sort
                my_script.save()
            except:
                pass

            # 起始 结束 点不在同一节点下 写入父节点名称与ID ?
            if parent != old_parent:
                return HttpResponse(script_parent.name + "^" + str(script_parent.id))
            else:
                return HttpResponse("0")


######################
# 场景配置
######################
@login_required
def process_design(request, funid):
    all_main_database = []
    all_hosts = DbCopyClient.objects.exclude(state="9").filter(hosttype="1")
    for host in all_hosts:
        all_main_database.append({
            "main_database_id": host.hostsmanage.id,
            "main_database_name": host.hostsmanage.host_name
        })

    # 选择关联客户端
    hosts = HostsManage.objects.exclude(state="9").filter(nodetype="CLIENT").values("id", "host_name")

    # 回切流程
    p_backs = Process.objects.exclude(state="9").filter(processtype=2).values("id", "name", "type", "pnode_id")

    return render(request, "processdesign.html", {
        'username': request.user.userinfo.fullname, 
        "pagefuns": getpagefuns(funid, request=request),
        'all_main_database': all_main_database, 
        'p_backs':p_backs,
        "hosts": [{
            "id": str(x["id"]),
            "host_name": x["host_name"]
        } for x in hosts],
    })


@login_required
def get_process_tree(request):
    status = 1
    info = ""
    data = []
    select_id = request.POST.get("id", "")

    try:
        root_nodes = Process.objects.order_by("sort").exclude(state="9").filter(pnode=None)
        for root_node in root_nodes:
            root = dict()
            root["text"] = root_node.name
            root["id"] = root_node.id
            root["data"] = {
                "pname": "无"
            }
            root["type"] = "NODE"
            try:
                if int(select_id) == root_node.id:
                    root["state"] = {"opened": True, "selected": True}
                else:
                    root["state"] = {"opened": True}
            except Exception as e:
                root["state"] = {"opened": True}
            root["children"] = get_process_node(root_node, select_id)
            data.append(root)
    except Exception as e:
        status = 0
        info = "获取流程树失败。"
    return JsonResponse({
        "status": status,
        "data": data,
        "info": info
    })


@login_required
def get_process_detail(request):
    status = 1
    info = ""
    data = {}

    process_id = request.POST.get("id", "")

    try:
        process_id = int(process_id)
        process = Process.objects.get(id=process_id)
    except Exception as e:
        status = 0
        info = "获取流程信息失败。"
    else:
        param_list = []
        try:
            config = etree.XML(process.config)

            param_el = config.xpath("//param")
            for v_param in param_el:
                param_list.append({
                    "param_name": v_param.attrib.get("param_name", ""),
                    "variable_name": v_param.attrib.get("variable_name", ""),
                    "param_value": v_param.attrib.get("param_value", ""),
                })
        except Exception as e:
            print(e)

        hosts_list = []
        try:
            associated_hosts = etree.XML(process.associated_hosts)

            host_el = associated_hosts.xpath("//host")
            for he in host_el:
                hosts_list.append({
                    "hosts_id": he.attrib.get("id", ""),
                    "hosts_name": he.attrib.get("name", ""),
                })
        except Exception as e:
            print(e)


        data = {
            "pname": process.pnode.name if process.pnode else "",
            "process_id": process.id,
            "process_code": process.code,
            "process_name": process.name,
            "process_remark": process.remark,
            "process_sign": process.sign,
            "process_rto": process.rto,
            "process_rpo": process.rpo,
            "process_sort": process.sort,
            "process_color": process.color,
            "type": process.type,
            "processtype": process.processtype,
            "variable_param_list": param_list,
            "hosts_list": hosts_list,
            "cv_client": process.hosts_id,
            "main_database": process.primary_id,
            "p_back": process.backprocess_id
        }

    return JsonResponse({
        "status": status,
        "data": data,
        "info": info
    })


@login_required
def process_move(request):
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
    old_process_parent = Process.objects.get(id=old_parent)
    old_sort = old_position + 1
    old_processs = Process.objects.exclude(state="9").filter(pnode=old_process_parent).filter(sort__gt=old_sort)

    # 目标节点下方(包括该节点) 所有节点 sort += 1
    process_parent = Process.objects.get(id=parent)
    sort = position + 1
    processs = Process.objects.exclude(state=9).exclude(id=id).filter(pnode=process_parent).filter(sort__gte=sort)

    my_process = Process.objects.get(id=id)

    # 判断目标父节点是否为接口，若为接口无法挪动
    if process_parent.type != "NODE" and my_process.processtype=="1":
        return HttpResponse("主场景")
    elif process_parent.type == "NODE" and my_process.type != "NODE" and my_process.processtype!="1" :
        return HttpResponse("子场景")
    else:
        # 目标父节点下所有节点 除了自身 接口名称都不得相同 否则重名
        process_same = Process.objects.exclude(state="9").exclude(id=id).filter(pnode=process_parent).filter(
            name=my_process.name)

        if process_same:
            return HttpResponse("重名")
        else:
            for old_process in old_processs:
                try:
                    old_process.sort -= 1
                    old_process.save()
                except:
                    pass
            for process in processs:
                try:
                    process.sort += 1
                    process.save()
                except:
                    pass

            # 该节点位置变动
            try:
                my_process.pnode = process_parent
                my_process.sort = sort
                my_process.save()
            except:
                pass

            # 起始 结束 点不在同一节点下 写入父节点名称与ID ?
            if parent != old_parent:
                return HttpResponse(process_parent.name + "^" + str(process_parent.id))
            else:
                return HttpResponse("0")


def get_process_node(parent, select_id):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9").exclude(Q(type=None) | Q(type=""))
    for child in children:
        node = dict()
        node["text"] = child.name
        node["id"] = child.id
        node["children"] = get_process_node(child, select_id)
        childtype=child.type
        if childtype != "NODE":
            childtype="PROCESS"
        node["type"] = childtype
        node["data"] = {
            "pname": parent.name,
            "name": child.name,
            "processtype": child.processtype,
            "remark": child.remark,
        }

        try:
            if int(select_id) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def process_save(request):
    status = 1
    info = "保存成功。"
    select_id = ""

    id = request.POST.get('id', '')
    pid = request.POST.get('pid', '')
    name = request.POST.get('name', '')
    remark = request.POST.get('remark', '')
    sign = request.POST.get('sign', '')
    rto = request.POST.get('rto', '')
    rpo = request.POST.get('rpo', '')
    sort = request.POST.get('sort', '')
    color = request.POST.get('process_color', '')
    cv_client = request.POST.get('cv_client', '')
    type = request.POST.get('type', '')
    nodetype = request.POST.get('my_type', '')
    processtype = request.POST.get('processtype', '')
    config = request.POST.get('config', "[]")
    associated_hosts = request.POST.get('associated_hosts', "[]")
    node_name = request.POST.get('node_name', '')
    node_remark = request.POST.get('node_name', '')

    try:
        id = int(id)
        pid = int(pid)
        cv_client = int(cv_client)
    except Exception as e:
        pass

    if nodetype == "NODE":
        if node_name.strip() == '':
            status = 0
            info = '节点名称不能为空。'
        else:
            if id == 0:
                try:
                    sort = 1
                    try:
                        max_sort = Process.objects.exclude(state="9").filter(pnode_id=pid).aggregate(
                            max_sort=Max('sort', distinct=True))["max_sort"]
                        sort = max_sort + 1
                    except:
                        pass
                    processsave = Process()
                    processsave.name = node_name
                    processsave.sort = sort if sort else None
                    processsave.remark = node_remark
                    processsave.type = "NODE"
                    processsave.pnode_id = pid

                    processsave.save()
                    name=node_name
                    select_id = processsave.id
                except Exception as e:
                    info = "保存失败：{0}".format(e)
                    status = 0
            else:
                # 修改
                try:
                    processsave = Process.objects.get(id=id)
                    processsave.name = node_name
                    processsave.remark = node_remark
                    processsave.save()
                    select_id = processsave.id
                except Exception as e:
                    info = "保存失败：{0}".format(e)
                    status = 0
    else:
        if name.strip() == '':
            info = '场景名称不能为空。'
            status = 0
        elif type.strip() == '':
            info = '场景类型不能为空。'
            status = 0
        elif sign.strip() == '':
            info = '是否签到不能为空。'
            status = 0
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
            xml_config = etree.tounicode(root)

            # 关联主机
            hosts_root = etree.Element("root")
            if associated_hosts:
                associated_hosts = json.loads(associated_hosts)
                for ah in associated_hosts:
                    hosts_node = etree.SubElement(hosts_root, "host")
                    if ah["hosts_id"]:
                        hosts_node.attrib["id"] = ah["hosts_id"]
                    else:
                        hosts_node.attrib["id"] = str(uuid.uuid1())
                    hosts_node.attrib["name"] = ah["hosts_name"]
            hosts_xml_config = etree.tounicode(hosts_root)

            if id == 0:
                try:
                    processsave = Process()
                    processsave.url = '/cv_oracler'
                    processsave.name = name
                    processsave.remark = remark
                    processsave.sign = sign
                    processsave.rto = rto if rto else None
                    processsave.rpo = rpo if rpo else None
                    processsave.sort = sort if sort else None
                    processsave.color = color
                    processsave.type = type
                    processsave.processtype = processtype
                    processsave.hosts_id = cv_client if cv_client else None
                    processsave.config = xml_config
                    processsave.associated_hosts = hosts_xml_config
                    processsave.pnode_id = pid

                    # 排序
                    sort = 1
                    try:
                        max_sort = Process.objects.exclude(state="9").filter(pnode_id=pid).aggregate(
                            max_sort=Max('sort', distinct=True))["max_sort"]
                        sort = max_sort + 1
                    except:
                        pass
                    processsave.sort = sort

                    processsave.save()
                    select_id = processsave.id
                except Exception as e:
                    info = "保存失败：{0}".format(e)
                    status = 0
            else:
                try:
                    processsave = Process.objects.get(id=id)
                    processsave.name = name
                    processsave.remark = remark
                    processsave.sign = sign
                    processsave.rto = rto if rto else None
                    processsave.rpo = rpo if rpo else None
                    processsave.sort = sort if sort else None
                    processsave.color = color
                    processsave.type = type
                    processsave.processtype = processtype
                    processsave.hosts_id = cv_client if cv_client else None
                    processsave.config = xml_config
                    processsave.associated_hosts = hosts_xml_config
                    processsave.save()
                    select_id = processsave.id
                except Exception as e:
                    info = "保存失败：{0}".format(e)
                    status = 0

    return JsonResponse({
        "status": status,
        "info": info,
        "data": select_id
    })


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


######################
# 流程配置
######################
@login_required
def processconfig(request, funid):
    process_id = request.GET.get("process_id", "")
    hosts_list = []
    try:
        process_id = int(process_id)
        cur_process = Process.objects.get(id=process_id)
        # 主机选项
        associated_hosts = etree.XML(cur_process.associated_hosts)
        hosts = associated_hosts.xpath("//host")
        hosts_list = [{
            "hosts_id": h.attrib.get("id", ""),
            "hosts_name": h.attrib.get("name", ""),
        } for h in hosts]
    except Exception as e:
        print(e)

    # tree_data
    select_id = ""
    tree_data = []
    root_nodes = Script.objects.order_by("sort").exclude(state="9").filter(pnode=None).filter(type="NODE")

    for root_node in root_nodes:
        root = dict()
        root["text"] = root_node.name
        root["id"] = root_node.id
        root["type"] = "NODE"
        root["data"] = {
            "remark": root_node.remark,
            "pname": "无"
        }
        root["a_attr"] = {
            "class": "jstree-no-checkboxes"
        }
        try:
            if int(select_id) == root_node.id:
                root["state"] = {"opened": True, "selected": True}
            else:
                root["state"] = {"opened": True}
        except:
            root["state"] = {"opened": True}
        root["children"] = get_script_node(root_node, select_id)
        tree_data.append(root)
    tree_data = json.dumps(tree_data, ensure_ascii=False)

    escape_dict = "{{}}"

    return render(request, 'processconfig.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                   "process_id": process_id, "hosts_list": hosts_list,
                   "tree_data": tree_data, "escape_dict": escape_dict})


@login_required
def processscriptsave(request):
    result = {}
    result["status"] = 1
    result["info"] = "保存脚本成功。"
    step_id = request.POST.get('step_id', '')
    script_id = request.POST.get('script_id', '')
    script_instance_id = request.POST.get('script_instance_id', '')
    config = request.POST.get('config', '')
    interface_type = request.POST.get('interface_type', '')  # 接口类型：Commvault Linux Windows
    error_solved = request.POST.get('error_solved', '')

    # add
    script_instance_name = request.POST.get('script_instance_name', '')  # 必填

    associated_hosts = request.POST.get('associated_hosts', '{}')

    try:
        associated_hosts = json.loads(associated_hosts)
    except:
        associated_hosts = {}

    log_address = request.POST.get('log_address', '')
    sort = request.POST.get('sort', '')
    script_instance_remark = request.POST.get('script_instance_remark', '')

    try:
        step_id = int(step_id)
    except:
        step_id = None
    try:
        script_id = int(script_id)
    except:
        script_id = None
    try:
        script_instance_id = int(script_instance_id)
    except:
        script_instance_id = None
    try:
        sort = int(sort)
    except:
        sort = None
    try:
        error_solved = int(error_solved)
    except:
        error_solved = None

    # 初始化
    if not script_instance_name:
        result["status"] = 0
        result["info"] = "接口实例名称未填写。"
    else:
        associated_hosts_xml = "</root>"
        if not associated_hosts:
            return JsonResponse({
                "status": 0,
                "info": "未选择主机"
            })
        else:
            try:
                hosts_root = etree.Element("root")
                hosts_node = etree.SubElement(hosts_root, "host")
                hosts_node.attrib["id"] = associated_hosts["hosts_id"]
                hosts_node.attrib["name"] = associated_hosts["hosts_name"]
                associated_hosts_xml = etree.tounicode(hosts_root)
            except Exception as e:
                print(e)

        if interface_type == "Commvault":
            create_data = {
                "params": config,
                "step_id": step_id,
                "script_id": script_id,
                "name": script_instance_name,
                "log_address": log_address,
                "sort": sort,
                "process_id": error_solved,
                "remark": script_instance_remark,
                "hosts_manage_id": None,
                "associated_hosts": associated_hosts_xml,
            }
        else:
            create_data = {
                "params": config,
                "step_id": step_id,
                "script_id": script_id,
                "name": script_instance_name,
                "log_address": log_address,
                "sort": sort,
                "process_id": error_solved,
                "remark": script_instance_remark,

                "utils_id": None,
                "primary_id": None,
                "associated_hosts": associated_hosts_xml,
            }

        try:
            step = Step.objects.get(id=int(step_id))
        except Exception as e:
            result["status"] = 0
            result["info"] = "保存脚本失败: {0}。".format(e)
        else:
            # 步骤在已有该脚本实例不可保存
            if script_instance_id:
                try:
                    ScriptInstance.objects.filter(id=script_instance_id).update(**create_data)
                    # 步骤下所有脚本
                    result["data"] = str(step.scriptinstance_set.exclude(state="9").values("id", "name"))
                    result["id"] = script_instance_id
                except Exception as e:
                    result["status"] = 0
                    result["info"] = "修改脚本失败: {0}。".format(e)
            else:
                try:
                    script_instance_id = ScriptInstance.objects.create(**create_data).id
                    # 步骤下所有脚本
                    result["data"] = str(step.scriptinstance_set.exclude(state="9").values("id", "name"))
                    result["id"] = script_instance_id
                except Exception as e:
                    result["status"] = 0
                    result["info"] = "新增脚本失败: {0}。".format(e)

    return JsonResponse(result)


@login_required
def get_script_data(request):
    """
    返回；
        接口信息
            接口编号
            接口名称
            接口类型
            脚本内容
            SUCCESSTEXT
            接口说明
        接口实例信息
            接口实例名称
            选择主机
            选择工具
            选择客户端
            填写类名
            日志地址
            接口实例说明
            参数值
    """
    status = 1
    info = '获取脚本信息成功。'
    data = []

    id = request.POST.get('id', '')
    try:
        id = int(id)
    except:
        status = 0
        info = '步骤未创建，请先保存步骤后添加脚本。'
    script_instance_id = request.POST.get("script_instance_id", "")
    try:
        script_instance = ScriptInstance.objects.get(id=int(script_instance_id))
    except:
        pass
    else:
        script = script_instance.script
        host_id = ""

        try:
            associated_hosts = etree.XML(script_instance.associated_hosts)
            host_id = associated_hosts.xpath("//host")[0].attrib.get("id", "")
        except Exception as e:
            print(e)

        data = {
            "script_id": script.id,
            "script_code": script.code,
            "script_name": script.name,
            "interface_type": script.interface_type,
            "commv_interface": script.commv_interface,
            "script_text": script.script_text,
            "succeedtext": script.succeedtext,
            "remark": script.remark,
            "type": script.type,
            "script_instance_id": script_instance.id,
            "script_instance_name": script_instance.name,
            "script_instance_remark": script_instance.remark,
            "script_instance_sort": script_instance.sort,
            "script_instance_error_solved": script_instance.process_id,
            "params": "",
            "log_address": script_instance.log_address,
            "host_id": host_id,
            "primary_id": script_instance.primary_id,
            "utils_id": script_instance.utils_id
        }

    return JsonResponse({
        'status': status,
        'info': info,
        'data': data,
    })


@login_required
def get_error_solved_process(request):
    """
    @params process_id
    """
    p_id = request.POST.get("process_id", "")

    status = 1
    info = "获取排错流程成功。"
    data = []
    try:
        p_id = int(p_id)
    except Exception as e:
        info = "获取排错流程失败。"
        status = 0
    else:
        data = Process.objects.exclude(state="9").filter(pnode_id=p_id,processtype="3").values("id", "name")

    return JsonResponse({
        "status": status,
        "info": info,
        "data": str(data)
    })


@login_required
def remove_script(request):
    status = 1
    info = "移除成功。"
    # 取消步骤中脚本的关联
    script_instance_id = request.POST.get("script_instance_id", "")
    try:
        script_instance = ScriptInstance.objects.filter(id=int(script_instance_id)).update(state="9")
    except Exception as e:
        print(e)
        status = 0
        info = "移除失败：{0}".format(e)
    return JsonResponse({
        "status": status,
        "info": info
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

        data = ""
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

            if time:
                try:
                    time = int(time)
                except:
                    time = None

            step.time = time if time != "" else None
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
                step[0].time = time if time != "" else None
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
            root["text"] = rootnode.name
            root["id"] = rootnode.id
            root["children"] = get_step_tree(rootnode, selectid)
            root["state"] = {"opened": True}
            treedata.append(root)
    process = {}
    process["text"] = process_name
    process["data"] = {"allgroups": group_string}
    process["children"] = treedata
    process["state"] = {"opened": True}
    return JsonResponse({"treedata": process})


@login_required
def get_step_detail(request):
    status = 1
    info = ""
    data = {}

    step_id = request.POST.get("id", "")

    try:
        cur_step = Step.objects.get(id=int(step_id))
    except Exception as e:
        status = 0
        info = "获取步骤信息失败。"
    else:
        scripts = cur_step.scriptinstance_set.exclude(state="9").order_by("sort")
        script_string = ""
        for script in scripts:
            id_code_plus = str(script.id) + "+" + str(script.name) + "&"
            script_string += id_code_plus

        verify_items_string = ""
        verify_items = cur_step.verifyitems_set.exclude(state="9")
        for verify_item in verify_items:
            id_name_plus = str(verify_item.id) + "+" + str(verify_item.name) + "&"
            verify_items_string += id_name_plus

        group_name = ""
        if cur_step.group and cur_step.group != " ":
            group_id = cur_step.group
            try:
                group_id = int(group_id)
                group_name = Group.objects.filter(id=group_id)[0].name
            except:
               pass

        all_groups = Group.objects.exclude(state="9")
        group_string = " " + "+" + " -------------- " + "&"
        for group in all_groups:
            id_name_plus = str(group.id) + "+" + str(group.name) + "&"
            group_string += id_name_plus

        data = {
            "time": cur_step.time, 
            "approval": cur_step.approval, 
            "skip": cur_step.skip, 
            "group_name": group_name,
            "group": cur_step.group, 
            "scripts": script_string, 
            "allgroups": group_string,
            "rto_count_in": cur_step.rto_count_in, 
            "remark": cur_step.remark,
            "verifyitems": verify_items_string, 
            "force_exec": cur_step.force_exec if cur_step.force_exec else 2
        }
    return JsonResponse({
        "status": status,
        "data": data,
        "info": info
    })


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
            group_info_dict = {
                "group_id": group.id,
                "group_name": group.name,
            }
            all_group_list.append(group_info_dict)
        return JsonResponse({"data": all_group_list})


def verify_items_save(request):
    if request.user.is_authenticated():
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
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            verify_id = request.POST.get("verify_id", "")
            all_verify_items = VerifyItems.objects.exclude(
                state="9").filter(id=verify_id)
            verify_data = ""
            if (len(all_verify_items) > 0):
                verify_data = {
                    "id": all_verify_items[0].id, "name": all_verify_items[0].name}
            return HttpResponse(json.dumps(verify_data))


def remove_verify_item(request):
    if request.user.is_authenticated():
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
def display_params(request):
    """
    参数： script_id, process_id
    响应：
        根据 脚本内容中 参数符号 从 主机参数、流程参数、脚本参数 匹配出 参数名称、变量、值、类别
    """
    status = 1
    data = []
    info = ""
    script_id = request.POST.get("script_id", "")
    script_instance_id = request.POST.get("script_instance_id", "")
    if_instance = request.POST.get("if_instance", "")
    process_id = request.POST.get("process_id", "")

    try:
        script = Script.objects.get(id=int(script_id))
    except:
        pass
    else:
        script_text = script.script_text

        if if_instance == "1":
            try:
                script_instance = ScriptInstance.objects.get(id=int(script_instance_id))
                cur_params = literal_eval(script_instance.params)
            except Exception as e:
                print(e)
            else:
                data = [{
                    "param_name": x["param_name"],
                    "variable_name": x["variable_name"],
                    "param_value": x["param_value"],
                    "type": x["type"]
                } for x in cur_params]

        else:
            script_param_list = get_params(script.config)
            script_variable_list = get_variable_name(script_text, "SCRIPT")
            for sv in script_variable_list:
                for sp in script_param_list:
                    if sv.strip() == sp["variable_name"]:
                        data.append({
                            "param_name": sp["param_name"],
                            "variable_name": sp["variable_name"],
                            "param_value": sp["param_value"],
                            "type": "SCRIPT"
                        })
                        break

    return JsonResponse({
        "status": status,
        "data": data,
        "info": info
    })


@login_required
def load_hosts_params(request):
    """
    流程配置
        切换主机，载入主机参数
    """
    host_id = request.POST.get("host_id", "")
    script_id = request.POST.get("script_id", "")
    data = []
    status = 1
    info = ""
    try:
        host = HostsManage.objects.get(id=int(host_id))
    except:
        stauts = 0
        info = "载入主机参数失败：主机不存在。"
    else:
        try:
            script = Script.objects.get(id=int(script_id))
        except:
            status = 0
            info = "载入主机参数失败：当前脚本不存在。"
        else:
            script_text = script.script_text

            # 主机参数
            host_param_list = get_params(host.config) if host else []
            host_variable_list = get_variable_name(script_text, "HOST")
            for hv in host_variable_list:
                for hp in host_param_list:
                    if hv.strip() == hp["variable_name"]:
                        data.append({
                            "param_name": hp["param_name"],
                            "variable_name": hp["variable_name"],
                            "param_value": hp["param_value"],
                            "type": "HOST"
                        })
                        break
    return JsonResponse({
        "status": status,
        "data": data,
        "info": info
    })

######################
# 流程计划
######################
def process_schedule(request, funid):
    if request.user.is_authenticated():
        all_process = Process.objects.exclude(state="9").exclude(Q(type=None) | Q(type="")| Q(type="NODE")).filter(processtype="1").order_by("sort").only("id", "name")

        p_params = []
        # 流程下包含客户端的默认参数
        for p in all_process:
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
            agent_type = ""
            all_steps = p.step_set.exclude(state="9")
            # all_steps = Step.objects.exclude(state="9").filter(process_id=process_id)
            if_break = False
            for cur_step in all_steps:
                all_scriptinstances = cur_step.scriptinstance_set.exclude(state="9")
                for cur_scriptinstance in all_scriptinstances:
                    pri = cur_scriptinstance.primary
                    if pri:
                        agent_type = pri.agentType
                        info = etree.XML(pri.info)
                        params = info.xpath("//param")

                        if params:
                            param = params[0]
                            std_id = pri.destination.id if pri.destination else ""
                            cv_params["pri_id"] = pri.id
                            cv_params["pri_name"] = pri.client_name
                            cv_params["std_id"] = std_id

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

                        if_break = True
                        break
                if if_break:
                    break

            p_params.append({
                "p_id": p.id,
                "p_type": p.type,
                "cv_params": cv_params,
                "agent_type": agent_type,
            })
        # 所有客户端
        cv_clients = CvClient.objects.exclude(state="9").values("id", "client_name")

        return render(request, 'process_schedule.html', {
            'username': request.user.userinfo.fullname,
            "pagefuns": getpagefuns(funid, request=request),
            "all_process": all_process,
            "cv_clients": cv_clients,
            "p_params": json.dumps(p_params, ensure_ascii=False)
        })
    else:
        return HttpResponseRedirect("/login")


def process_schedule_save(request):
    if request.user.is_authenticated():
        process_schedule_id = request.POST.get('process_schedule_id', '')
        process_schedule_name = request.POST.get('process_schedule_name', '')
        pro_ins_id = request.POST.get('pro_ins_id', '')
        process_schedule_remark = request.POST.get('process_schedule_remark', '')

        schedule_type = request.POST.get('schedule_type', '')

        per_time = request.POST.get('per_time', '')
        per_month = request.POST.get('per_month', '')
        per_week = request.POST.get('per_week', '')

        # 流程参数
        # Commvault
        agent_type = request.POST.get('agent_type', '')

        pri = request.POST.get('pri', '')
        pri_name = request.POST.get('pri_name', '')
        std = request.POST.get('std', '')
        recovery_time = request.POST.get('recovery_time', '')
        browseJobId = request.POST.get('browseJobId', '')
        # Oracle
        data_path = request.POST.get('data_path', '')
        copy_priority = request.POST.get('copy_priority', '')
        db_open = request.POST.get('db_open', '')
        log_restore = request.POST.get('log_restore', '')
        # File System
        mypath = request.POST.get("mypath", "")
        iscover = request.POST.get("iscover", "")
        selectedfile = request.POST.get("selectedfile", "")
        # SQL Server
        mssql_iscover = request.POST.get("mssql_iscover", "")

        ret = 1
        info = ""

        if not process_schedule_name:
            return JsonResponse({
                "ret": 0,
                "info": "计划名称不能为空。"
            })

        try:
            pro_ins_id = int(pro_ins_id)
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
            cur_process = ProcessInstance.objects.get(id=pro_ins_id)
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

                cv_params = {}
                # 传入流程参数
                if cur_process.process.type == "Commvault":
                    try:
                        pri = int(pri)
                    except Exception:
                        return JsonResponse({
                            "ret": 0,
                            "info": "流程步骤中未添加Commvault接口，导致源客户端未空。"
                        })

                    try:
                        std = int(std)
                    except:
                        return JsonResponse({
                            "ret": 0,
                            "info": "目标客户端未选择。"
                        })

                    if "Oracle" in agent_type:
                        try:
                            copy_priority = int(copy_priority)
                        except ValueError as e:
                            copy_priority = 1
                        try:
                            db_open = int(db_open)
                        except ValueError as e:
                            db_open = 1
                        try:
                            log_restore = int(log_restore)
                        except ValueError as e:
                            log_restore = 1
                        cv_params = {
                            "pri_id": str(pri),
                            "pri_name": pri_name,
                            "std_id": str(std),
                            "browse_job_id": str(browseJobId),
                            "recovery_time": recovery_time,

                            "copy_priority": str(copy_priority),
                            "db_open": str(db_open),
                            "log_restore": str(log_restore),
                            "data_path": data_path
                        }
                    elif "File System" in agent_type:
                        inPlace = True
                        if mypath != "same":
                            inPlace = False
                        overWrite = False
                        if iscover == "TRUE":
                            overWrite = True

                        sourceItemlist = selectedfile.split("*!-!*")
                        for sourceItem in sourceItemlist:
                            if sourceItem == "":
                                sourceItemlist.remove(sourceItem)
                        cv_params = {
                            "pri_id": str(pri),
                            "pri_name": pri_name,
                            "std_id": str(std),
                            "browse_job_id": str(browseJobId),
                            "recovery_time": recovery_time,

                            "overWrite": overWrite,
                            "inPlace": inPlace,
                            "destPath": mypath,
                            "sourcePaths": sourceItemlist,
                            "OSRestore": False
                        }
                    elif "SQL Server" in agent_type:
                        mssqlOverWrite = False
                        if mssql_iscover == "TRUE":
                            mssqlOverWrite = True
                        cv_params = {
                            "pri_id": str(pri),
                            "pri_name": pri_name,
                            "std_id": str(std),
                            "browse_job_id": str(browseJobId),
                            "recovery_time": recovery_time,

                            "mssqlOverWrite": mssqlOverWrite,
                        }
                    else:
                        return JsonResponse({
                            'ret': 0,
                            'info': '其他应用正在开发中。'
                        })


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
                    cur_periodictask.kwargs = json.dumps({
                        'cur_process': cur_process.id,
                        'creatuser':  request.user.username,
                        'cv_params': cv_params,
                        "agent_type": agent_type,
                    })
                    cur_periodictask.save()
                    cur_periodictask_id = cur_periodictask.id

                    ps = ProcessSchedule()
                    ps.dj_periodictask_id = cur_periodictask_id
                    ps.pro_ins = cur_process
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
                                'creatuser':  request.user.username,
                                'cv_params': cv_params,
                                "agent_type": agent_type,
                            })
                            cur_periodictask_status = cur_periodictask.enabled
                            cur_periodictask.enabled = cur_periodictask_status
                            cur_periodictask.save()

                            ps.pro_ins = cur_process
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
    else:
        return HttpResponseRedirect("/login")


def process_schedule_data(request):
    if request.user.is_authenticated():
        result = []

        pro_ins_id = request.GET.get('pro_ins_id', '')

        try:
            pro_ins_id = int(pro_ins_id)
        except ValueError:
            pass
        else:
            all_process_schedules = ProcessSchedule.objects.filter(pro_ins_id=pro_ins_id).exclude(state="9").select_related("pro_ins", "process", "dj_periodictask", "dj_periodictask__crontab")

            for process_schedule in all_process_schedules:
                remark = process_schedule.remark
                schedule_type = process_schedule.schedule_type
                schedule_type_display = process_schedule.get_schedule_type_display()
                # 定时任务
                status, minutes, hours, per_week, per_month = "", "", "", "", ""
                periodictask = process_schedule.dj_periodictask
                cv_params = {}
                agent_type = ""
                if periodictask:
                    status = periodictask.enabled
                    cur_crontab_schedule = periodictask.crontab
                    try:
                        kwargs = json.loads(periodictask.kwargs)
                        cv_params = kwargs.get("cv_params", "")
                        agent_type = kwargs.get("agent_type", "")
                    except Exception as e:
                        print(e)

                    if cur_crontab_schedule:
                        minutes = cur_crontab_schedule.minute
                        hours = cur_crontab_schedule.hour
                        per_week = cur_crontab_schedule.day_of_week
                        per_month = cur_crontab_schedule.day_of_month

                result.append({
                    "process_schedule_id": process_schedule.id,
                    "process_schedule_name": process_schedule.name,
                    "remark": remark,
                    "schedule_type": schedule_type,
                    "schedule_type_display": schedule_type_display,
                    "minutes": minutes,
                    "hours": hours,
                    "per_week": per_week,
                    "per_month": per_month,
                    "status": status,

                    # Commvault参数
                    "p_type": process_schedule.pro_ins.process.type,
                    "cv_params": cv_params,
                    "agent_type": agent_type,
                })
        return JsonResponse({"data": result})
    else:
        return HttpResponseRedirect("/login")


def change_periodictask(request):
    if request.user.is_authenticated():
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
    else:
        return HttpResponseRedirect("/login")


def process_schedule_del(request):
    if request.user.is_authenticated():
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
    else:
        return HttpResponseRedirect("/login")


######################
# 工具管理
######################
@login_required
def util_manage(request, funid):
    return render(request, 'util_manage.html',
                  {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})



@login_required
def util_manage_data(request):
    """
    工具管理信息
    """
    util_manage_list = []

    util_manages = UtilsManage.objects.exclude(state='9')

    for um in util_manages:
        if um.util_type.upper() == 'COMMVAULT':
            commvault_credit, sqlserver_credit = get_credit_info(um.content, um.util_type.upper())
            util_manage_list.append({
                'id': um.id,
                'code': um.code,
                'name': um.name,
                'util_type': um.util_type,
                'commvault_credit': commvault_credit,
                'sqlserver_credit': sqlserver_credit,
            })

        elif um.util_type.upper() == 'KVM':
            kvm_credit = get_credit_info(um.content, um.util_type.upper())
            util_manage_list.append({
                'id': um.id,
                'code': um.code,
                'name': um.name,
                'util_type': um.util_type,
                'kvm_credit': kvm_credit
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

    KvmHost = request.POST.get('KvmHost', '')
    KvmUser = request.POST.get('KvmUser', '')
    KvmPasswd = request.POST.get('KvmPasswd', '')
    SystemType = request.POST.get('SystemType', '')

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
            elif util_type.strip().upper() == 'KVM':
                credit = """<?xml version="1.0" ?>
                    <vendor>
                        <KvmHost>{KvmHost}</KvmHost>
                        <KvmUser>{KvmUser}</KvmUser>
                        <KvmPasswd>{KvmPasswd}</KvmPasswd>
                        <SystemType>{SystemType}</SystemType>
                    </vendor>""".format(**{
                    "KvmHost": KvmHost,
                    "KvmUser": KvmUser,
                    "KvmPasswd": base64.b64encode(KvmPasswd.encode()).decode(),
                    "SystemType": SystemType
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


######################
# 接口配置
######################
def get_script_node(parent, select_id):
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
                "pname": parent.name,
                "name": child.name
            }
            node["a_attr"] = {
                "class": "jstree-no-checkboxes"
            }
        if child.type == "INTERFACE":  # 接口
            # 脚本参数
            param_list = []
            try:
                config = etree.XML(child.config)

                param_el = config.xpath("//param")
                for v_param in param_el:
                    param_list.append({
                        "param_name": v_param.attrib.get("param_name", ""),
                        "variable_name": v_param.attrib.get("variable_name", ""),
                        "param_value": v_param.attrib.get("param_value", ""),
                    })
            except Exception as e:
                print(e)

            node["data"] = {
                "pname": parent.name,
                "remark": child.remark,
                "code": child.code,
                "name": child.name,
                "type": child.type,
                "interface_type": child.interface_type,
                "commv_interface": child.commv_interface,
                "script_text": child.script_text,
                "success_text": child.succeedtext,
                "variable_param_list": param_list,
            }
        node["children"] = get_script_node(child, select_id)
        try:
            if int(select_id) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


@login_required
def script(request, funid):
    escape_dict = "{{}}"
    return render(request, 'script.html', {
        'username': request.user.userinfo.fullname,
        "pagefuns": getpagefuns(funid, request=request),
        "escape_dict": escape_dict
    })


@login_required
def get_script_tree(request):
    status = 1
    info = ""
    data = []
    select_id = request.POST.get("id", )
    root_nodes = Script.objects.order_by("sort").exclude(state="9").filter(pnode=None).filter(type="NODE")

    for root_node in root_nodes:
        root = dict()
        root["text"] = root_node.name
        root["id"] = root_node.id
        root["type"] = "NODE"
        root["data"] = {
            "remark": root_node.remark,
            "pname": "无"
        }
        try:
            if int(select_id) == root_node.id:
                root["state"] = {"opened": True, "selected": True}
            else:
                root["state"] = {"opened": True}
        except:
            root["state"] = {"opened": True}
        root["children"] = get_script_node(root_node, select_id)
        data.append(root)
    return JsonResponse({
        "status": status,
        "info": info,
        "data": data
    })
