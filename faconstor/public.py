import re
from ast import literal_eval
from lxml import etree
from .models import (
    HostsManage
)
import base64


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
