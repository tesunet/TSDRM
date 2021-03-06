import re
from ast import literal_eval
from lxml import etree
import base64
import requests
import json

from .models import *
from celery.app.control import Control
from TSDRM.celery import app


def revoke_p_task(pr_id):
    """
    中止指定流程所有taskid：name=faconstor.tasks.exec_process的最新任务中止
    return status{bool}: 1 成功 2 失败 0 任务不存在
    """
    status = 0
    try:
        task_url = "http://127.0.0.1:5555/api/tasks"

        try:
            task_json_info = requests.get(task_url).text
        except:
            status = 2
        else:
            task_dict_info = json.loads(task_json_info)
            c_control = Control(app=app)

            for key, value in task_dict_info.items():
                try:
                    task_process_id = int(value["args"][1:-1])
                except:
                    task_process_id = ""
                # 终止指定流程的异步任务
                if task_process_id == pr_id and value["name"] == "faconstor.tasks.exec_process":
                    task_id = key
                    print(key)
                    c_control.revoke(str(task_id), terminate=True)
                    status = 1
    except Exception as e:
        print(e)
        status = 2
    if status == 1:  # 修改processrun.walkthoughstate
        try:
            ProcessRun.objects.filter(id=pr_id).update(**{
                "walkthroughstate": "STOP"
            })
        except:
            pass
    return status


def is_p_task_exists(pr_id):
    """
    查看当前流程是否存在任务
    return status{bool}: 1 存在 0 不存在
    """
    status = 0
    try:
        task_url = "http://127.0.0.1:5555/api/tasks"

        try:
            task_json_info = requests.get(task_url).text
        except:
            status = 0
        else:
            task_dict_info = json.loads(task_json_info)

            for _, value in task_dict_info.items():
                try:
                    task_process_id = int(value["args"][1:-1])
                except:
                    task_process_id = ""
                # 终止指定流程的异步任务
                if task_process_id == pr_id and value["name"] == "faconstor.tasks.exec_process":
                    status = 1
                    break
    except Exception as e:
        print(e)
        status = 0
    return status


def get_params(config, add_type=None):
    """
    <root>
        <param param_name="1" variable_name="2" param_value="3"/>
        <param param_name="3" variable_name="4" param_value="5"/>
        <param param_name="5" variable_name="6" param_value="7"/>
    </root>
    """
    param_list = []
    pre_config = "<root></root>"
    if config:
        config = etree.XML(config)
    else:
        config = etree.XML(pre_config)
    param_nodes = config.xpath("//param")
    for pn in param_nodes:
        if not add_type:
            param_list.append({
                "param_name": pn.attrib.get("param_name", ""),
                "variable_name": pn.attrib.get("variable_name", ""),
                "param_value": pn.attrib.get("param_value", ""),
            })
        else:
            param_list.append({
                "param_name": pn.attrib.get("param_name", ""),
                "variable_name": pn.attrib.get("variable_name", ""),
                "param_value": pn.attrib.get("param_value", ""),
                "type": add_type
            })
    return param_list


def get_variable_name(content, param_type):
    """
    MATCH PARAM NAME FROM SYMBOLS {{}} [[]] (())
    :param content:
    :param param_type:
    :return:
    """
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
    """
    GET VALUE FROM PARAMS{JSON}
    :param variable_name:
    :param params:
    :return:
    """
    param_value = ""
    for param in params:
        if variable_name.strip() == param["variable_name"]:
            param_value = param["param_value"]
            break
    return str(param_value) if param_value else ""


def content_load_params(script_instance, process_instance):
    """
    @param script_instance: 脚本实例
    @param process_instance: 流程实例
    脚本中传入参数
        接口参数 ScriptInstance->params
        主机参数 HostsManage->config + HostsManage(表所有字段信息) + CvClient(表所有字段信息)
        流程参数 ProcessInstance->config
    :return: 整合参数后脚本内容
    """
    # 1.接口参数：[{"param_name":"SCRIPT","variable_name":"S1","param_value":"SV1","type":"SCRIPT"}]
    params = literal_eval(script_instance.params)

    # ScriptInstance.associated_host->ProcessInstance.config->host_id
    associated_host = match_host(script_instance, process_instance)
    if associated_host:
        # 2.主机参数
        host_params = get_params(associated_host.config, add_type='HOST')
        params.extend(host_params)
        # 3.流程参数(*)
        #   排错流程配置使用主流程配置
        p_ins_config = process_instance.config
        if process_instance.pnode:
            p_ins_config = process_instance.pnode.config

        pro_ins_params = get_params(p_ins_config, add_type="PROCESS")
        params.extend(pro_ins_params)
        # 4.特定主机参数
        # 特定参数 -> HostsManage CvClient 表字段
        hm_spc = {  # 特定主机参数(字段)
            "_host_ip": associated_host.host_ip,
            "_host_name": associated_host.host_name,
            "_host_os": associated_host.os,
            "_host_type": associated_host.type,
            "_host_username": associated_host.username,
            "_host_password": associated_host.password,
        }
        hm_spc_params = [{
            "variable_name": k,
            "param_value": v,
            "type": "HOST",
        } for k, v in hm_spc.items() if k]
        hm_cfg_params = get_params(associated_host.config, add_type="HOST")  # 主机参数

        params.extend(hm_spc_params)
        params.extend(hm_cfg_params)
        hms = associated_host.cvclient_set.exclude(state="9")
        cv_cli = hms[0] if hms.exists() else ""  # 主机下的客户端
        if cv_cli:
            cv_cli_spc = {  # 特定客户端参数(字段)
                "_cv_cli_id": cv_cli.client_id,
                "_cv_cli_name": cv_cli.client_name,
                "_cv_cli_agentType": cv_cli.agentType,
                "_cv_cli_instanceName": cv_cli.instanceName,
                "_cv_cli_std_id": cv_cli.destination.client_id if cv_cli.destination else "",
                "_cv_cli_std_name": cv_cli.destination.client_name if cv_cli.destination else ""
            }
            cv_cli_spc_params = [{
                "variable_name": k,
                "param_value": v,
                "type": "HOST",
            } for k, v in cv_cli_spc.items() if k]
            params.extend(cv_cli_spc_params)

    script = script_instance.script
    script_text = script.script_text
    # 处理流程参数
    process_variable_list, process_variable_list_with_symbol = get_variable_name(script_text, "PROCESS")
    for n, pv in enumerate(process_variable_list):
        param_value = get_value_from_params(pv, params)
        script_text = script_text.replace(process_variable_list_with_symbol[n], param_value)
    # 处理主机参数
    host_variable_list, host_variable_list_with_symbol = get_variable_name(script_text, "HOST")
    for n, hv in enumerate(host_variable_list):
        param_value = get_value_from_params(hv, params)
        script_text = script_text.replace(host_variable_list_with_symbol[n], param_value)
    # 处理脚本参数
    script_variable_list, script_variable_list_with_symbol = get_variable_name(script_text, "SCRIPT")  # 获取脚本实例相关参数名称
    for n, sv in enumerate(script_variable_list):
        param_value = get_value_from_params(sv, params)  # 从参数键值字典中获取参数的值
        script_text = script_text.replace(script_variable_list_with_symbol[n], param_value)  # 替换参数值

    return script_text


def match_host(script_instance, process_instance):
    """
    接口实例中关联主机uuid匹配，从流程实例中匹配出HostsManage对象
    附：排错流程实例使用主流程实例的config
    @param script_instance:
    @param process_instance:
    :return: associated_host
    """
    associated_host = None
    try:
        associated_host_root = etree.XML(script_instance.associated_hosts)
        associated_host_els = associated_host_root.xpath('//host')
        if associated_host_els:
            associated_host_el = associated_host_els[0]
            associated_host_uuid = associated_host_el.attrib.get('id', '')

            # 从pro_ins.config匹配对应的HOST_ID
            associated_host_id = None

            config = process_instance.config
            if process_instance.pnode:  # 排错流程实例使用主流程实例的配置
                config = process_instance.pnode.config

            config_root = etree.XML(config)
            config_els = config_root.xpath('//host')
            for config_el in config_els:
                if associated_host_uuid == config_el.attrib.get('host_uuid', '') and associated_host_uuid:
                    associated_host_id = config_el.attrib.get('host_id', '')
                    break
            associated_host = HostsManage.objects.get(id=int(associated_host_id))
    except:
        pass
    return associated_host


def get_credit_info(content, util_type="COMMVAULT"):
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
    kvm_credit = {
        'KvmHost': '',
        'KvmUser': '',
        'KvmPasswd': '',
        'SystemType': '',
    }
    falconstor_credit = {
        'falconstor_webaddr': '',
        'falconstor_hostusernm': '',
        'falconstor_hostpasswd': '',
    }
    try:
        doc = etree.XML(content)
        if util_type == 'COMMVAULT':
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

            return commvault_credit, sqlserver_credit
        elif util_type == 'KVM':
            # Kvm账户信息
            try:
                kvm_credit['KvmHost'] = doc.xpath('//KvmHost/text()')[0]
            except:
                pass
            try:
                kvm_credit['KvmUser'] = doc.xpath('//KvmUser/text()')[0]
            except:
                pass
            try:
                kvm_credit['KvmPasswd'] = base64.b64decode(
                    doc.xpath('//KvmPasswd/text()')[0]).decode()
            except:
                pass
            try:
                kvm_credit['SystemType'] = doc.xpath('//SystemType/text()')[0]
            except:
                pass
            return kvm_credit
        elif util_type == "FALCONSTOR":
            try:
                falconstor_credit['falconstor_webaddr'] = doc.xpath('//falconstor_webaddr/text()')[0]
            except:
                pass
            try:
                falconstor_credit['falconstor_hostusernm'] = doc.xpath('//falconstor_hostusernm/text()')[0]
            except:
                pass
            try:
                falconstor_credit['falconstor_hostpasswd'] = base64.b64decode(
                    doc.xpath('//falconstor_hostpasswd/text()')[0]).decode()
            except:
                pass
            return falconstor_credit
    except Exception as e:
        print(e)


def file_iterator(file_name, chunk_size=512):
    with open(file_name, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def get_params_from_pro_ins(pro_ins_id):
    """
    从流程实例获取Commvault恢复所需参数
    @param pro_ins_id:
    :return: agent_type, std_id, cv_params
    """
    # 1.流程配置中源端ID与名称,以及默认源端关联的终端ID
    # 2.所有客户端ID与名称
    # 3.Oracle恢复需要的参数
    # pri, std, data_path, copy_priority, db_open, log_restore
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
    std_id = ""
    try:
        pro_ins_id = int(pro_ins_id)
        pro_ins = ProcessInstance.objects.get(id=pro_ins_id)
        config_root = etree.XML(pro_ins.config)
        # HOST -> CVCLIENT -> CV_PARAMS
        hosts = config_root.xpath('//host')
        for host in hosts:
            host_id = host.attrib.get('host_id', '')
            host_uuid = host.attrib.get('host_uuid', '')
            try:
                host_id = int(host_id)
            except:
                pass
            cv_clients = CvClient.objects.exclude(state='9').filter(hostsmanage_id=host_id)
            if cv_clients.exists() and is_commvault_script(host_uuid):
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
    return agent_type, std_id, cv_params


def is_ipv4(ip):
    """
    检查ip是否合法
    @param ip{str}: ip地址
    @return legal{bool}: True 合法 False 不合法
    """
    legal = True

    try:
        assert len([x for x in ip.split(".") if int(x) < 255]) == 4
    except:
        legal = False
    return legal


def is_commvault_script(host_uuid):
    """
    判断接口实例对应的接口是否为commvault类型
    @param host_uuid{str}:
    @return status{bool}:
    """
    status = False
    script_instances = ScriptInstance.objects.exclude(state='9')
    for script_ins in script_instances:
        try:
            associated_root = etree.XML(script_ins.associated_hosts)
        except:
            pass
        else:
            associated_hosts = associated_root.xpath('//host')
            for associated_host in associated_hosts:
                id = associated_host.attrib.get('id', '')
                if host_uuid == id and script_ins.script.interface_type == "Commvault":
                    status = True
                    break
    return status


