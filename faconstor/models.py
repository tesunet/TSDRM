# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    name = models.CharField(u"组名", blank=True, null=True, max_length=50)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)


class UserInfo(models.Model):
    client_host = models.ManyToManyField("ClientHost")
    group = models.ManyToManyField(Group)
    user = models.OneToOneField(User, blank=True, null=True)
    userGUID = models.CharField("GUID", null=True, max_length=50)
    fullname = models.CharField("姓名", blank=True, max_length=50)
    phone = models.CharField("电话", blank=True, null=True, max_length=50)
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    type = models.CharField("类型", blank=True, null=True, max_length=20)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    company = models.CharField("公司", blank=True, null=True, max_length=100)
    tell = models.CharField("电话", blank=True, null=True, max_length=50)
    forgetpassword = models.CharField("修改密码地址", blank=True, null=True, max_length=50)


class Process(models.Model):
    code = models.CharField(u"预案编号", blank=True, max_length=50)
    name = models.CharField(u"预案名称", blank=True, max_length=50)
    remark = models.CharField(u"预案描述", blank=True, null=True, max_length=5000)
    sign = models.CharField(u"是否签到", blank=True, null=True, max_length=20)
    rto = models.IntegerField(u"RTO", blank=True, null=True)
    rpo = models.IntegerField(u"RPO", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    url = models.CharField(u"页面链接", blank=True, max_length=100)
    type = models.CharField(u"预案类型", blank=True, max_length=100, null=True)


class Step(models.Model):
    process = models.ForeignKey(Process)
    last = models.ForeignKey('self', blank=True, null=True, related_name='next', verbose_name='上一步')
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    code = models.CharField(u"步骤编号", blank=True, null=True, max_length=50)
    name = models.CharField(u"步骤名称", blank=True, null=True, max_length=50)
    approval = models.CharField(u"是否审批", blank=True, null=True, max_length=10)
    skip = models.CharField(u"能否跳过", blank=True, null=True, max_length=10)
    group = models.CharField(u"角色", blank=True, null=True, max_length=50)
    time = models.IntegerField(u"预计耗时", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=10)
    sort = models.IntegerField(u"排序", blank=True, null=True)


class Script(models.Model):
    step = models.ForeignKey(Step, blank=True, null=True)
    code = models.CharField(u"脚本编号", blank=True, max_length=50)
    name = models.CharField(u"脚本名称", blank=True, max_length=500)
    ip = models.CharField(u"主机IP", blank=True, null=True, max_length=50)
    port = models.CharField(u"端口号", blank=True, null=True, max_length=10)
    type = models.CharField(u"连接类型", blank=True, null=True, max_length=20)
    runtype = models.CharField(u"运行类型", blank=True, null=True, max_length=20)
    username = models.CharField(u"用户名", blank=True, null=True, max_length=50)
    password = models.CharField(u"密码", blank=True, null=True, max_length=50)
    filename = models.CharField(u"脚本文件名", blank=True, null=True, max_length=50)
    paramtype = models.CharField(u"参数类型", blank=True, null=True, max_length=20)
    param = models.CharField(u"脚本参数", blank=True, null=True, max_length=100)
    scriptpath = models.CharField(u"脚本文件路径", blank=True, null=True, max_length=100)
    runpath = models.CharField(u"执行路径", blank=True, null=True, max_length=100)
    command = models.CharField(u"生产命令行", blank=True, null=True, max_length=500)
    maxtime = models.IntegerField(u"超时时间", blank=True, null=True)
    time = models.IntegerField(u"预计耗时", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    succeedtext = models.CharField("成功代码", blank=True, null=True, max_length=500)


class ResourcePool(models.Model):
    name = models.CharField("名称", blank=True, max_length=50)
    type = models.CharField("类型", blank=True, null=True, max_length=20)
    supplier = models.CharField("供应商", blank=True, null=True, max_length=50)
    certificate = models.CharField("证书", blank=True, null=True, max_length=5000)
    specifications = models.CharField("规格", blank=True, null=True, max_length=5000)
    description = models.CharField("描述", blank=True, null=True, max_length=50)
    level = models.CharField("级别", blank=True, null=True, max_length=10)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    creatdate = models.DateTimeField("创建时间", blank=True, null=True)
    updatedate = models.DateTimeField("修改时间", blank=True, null=True)


class ComputerResource(models.Model):
    name = models.CharField("名称", blank=True, max_length=50)
    pool = models.ForeignKey(ResourcePool, blank=True, null=True)
    certificate = models.CharField("证书", blank=True, null=True, max_length=5000)
    specifications = models.CharField("规格", blank=True, null=True, max_length=5000)
    cost = models.IntegerField("成本", blank=True, null=True)
    description = models.CharField("描述", blank=True, null=True, max_length=50)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    creatdate = models.DateTimeField("创建时间", blank=True, null=True)
    updatedate = models.DateTimeField("修改时间", blank=True, null=True)


class VmResource(models.Model):
    pool = models.ForeignKey(ResourcePool, blank=True, null=True)
    name = models.CharField("名称", blank=True, max_length=50)
    template_name = models.CharField("模板名称", blank=True, max_length=50)
    system = models.CharField("系统", blank=True, max_length=50)
    specifications = models.CharField("规格", blank=True, null=True, max_length=5000)
    description = models.CharField("描述", blank=True, null=True, max_length=50)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    vm_num = models.IntegerField("虚机数", blank=True, null=True)
    uuid = models.CharField("uuid", blank=True, null=True, max_length=256)
    vm_type = models.CharField("虚机类型", blank=True, null=True, max_length=50)
    template = models.ForeignKey("self", blank=True, null=True, verbose_name="模板")
    creatdate = models.DateTimeField("创建时间", blank=True, null=True)
    updatedate = models.DateTimeField("修改时间", blank=True, null=True)

    class Meta:
        verbose_name = "虚机资源"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class BackupResource(models.Model):
    name = models.CharField("名称", blank=True, max_length=50)
    pool = models.ForeignKey(ResourcePool, blank=True, null=True)
    certificate = models.CharField("证书", blank=True, null=True, max_length=5000)
    specifications = models.CharField("规格", blank=True, null=True, max_length=5000)
    cost = models.IntegerField("成本", blank=True, null=True)
    description = models.CharField("描述", blank=True, null=True, max_length=50)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    creatdate = models.DateTimeField("创建时间", blank=True, null=True)
    updatedate = models.DateTimeField("修改时间", blank=True, null=True)


class SchduleResource(models.Model):
    name = models.CharField("名称", blank=True, max_length=50)
    pool = models.ForeignKey(ResourcePool, blank=True, null=True)
    certificate = models.CharField("证书", blank=True, null=True, max_length=5000)
    specifications = models.CharField("规格", blank=True, null=True, max_length=5000)
    cost = models.IntegerField("成本", blank=True, null=True)
    description = models.CharField("描述", blank=True, null=True, max_length=50)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    creatdate = models.DateTimeField("创建时间", blank=True, null=True)
    updatedate = models.DateTimeField("修改时间", blank=True, null=True)


class ClientHost(models.Model):
    clientGUID = models.CharField("GUID", null=True, max_length=50)
    clientName = models.CharField("主机名称", max_length=200)
    owernID = models.CharField("用户GUID", blank=True, null=True, max_length=50)
    hostType = models.CharField("主机类型", blank=True, null=True, max_length=50)
    vendor = models.CharField("vendor", blank=True, null=True, max_length=1000)
    zone = models.CharField("zone", blank=True, null=True, max_length=1000)
    clientID = models.IntegerField("主机ID", blank=True, null=True)
    proxyClientID = models.CharField("代理主机列表", blank=True, null=True, max_length=5000)
    creditInfo = models.CharField("认证信息", blank=True, null=True, max_length=1000)
    agentTypeList = models.CharField("代理类型列表", blank=True, null=True, max_length=2000)
    status = models.CharField("状态", blank=True, null=True, max_length=20)
    platform = models.CharField("平台", blank=True, null=True, max_length=50)
    appGroup = models.CharField("应用组", blank=True, null=True, max_length=50)
    comment = models.CharField("描述", blank=True, null=True, max_length=1000)
    installTime = models.DateTimeField("安装时间", blank=True, null=True)
    activeTime = models.DateTimeField("激活时间", blank=True, null=True)
    firstProtectTime = models.DateTimeField("首次保护时间", blank=True, null=True)
    lastProtectTime = models.DateTimeField("最近保护时间", blank=True, null=True)


class DataSet(models.Model):
    dataSetGUID = models.CharField("GUID", null=True, max_length=50)
    clientGUID = models.CharField("主机GUID", null=True, max_length=50)
    clientName = models.CharField("主机名称", max_length=200)
    owernID = models.CharField("用户GUID", blank=True, null=True, max_length=50)
    vendor = models.CharField("vendor", blank=True, null=True, max_length=1000)
    zone = models.CharField("zone", blank=True, null=True, max_length=1000)
    clientID = models.IntegerField("主机ID", blank=True, null=True)
    instanceName = models.CharField("实例名称", blank=True, null=True, max_length=500)
    agentType = models.CharField("代理类型", blank=True, null=True, max_length=50)
    credit = models.CharField("认证信息", blank=True, null=True, max_length=1000)
    status = models.CharField("状态", blank=True, null=True, max_length=20)
    appGroup = models.CharField("应用组名称", blank=True, null=True, max_length=50)
    comment = models.CharField("描述", blank=True, null=True, max_length=1000)
    content = models.CharField("保护内容", blank=True, null=True, max_length=5000)
    installTime = models.DateTimeField("安装时间", blank=True, null=True)
    activeTime = models.DateTimeField("激活时间", blank=True, null=True)
    firstProtectTime = models.DateTimeField("首次保护时间", blank=True, null=True)
    lastProtectTime = models.DateTimeField("最近保护时间", blank=True, null=True)


class Vendor(models.Model):
    vendorGUID = models.CharField("GUID", null=True, max_length=50)
    name = models.CharField("名称", blank=True, null=True, max_length=50)
    type = models.CharField("类型", blank=True, null=True, max_length=50)
    content = models.CharField("内容", blank=True, null=True, max_length=5000)
    status = models.CharField("状态", blank=True, null=True, max_length=20)


class Joblist(models.Model):
    jobid = models.IntegerField("任务ID")


class ProcessRun(models.Model):
    process = models.ForeignKey(Process)
    DataSet = models.ForeignKey(DataSet, blank=True, null=True)
    starttime = models.DateTimeField(u"开始时间", blank=True, null=True)
    endtime = models.DateTimeField(u"结束时间", blank=True, null=True)
    creatuser = models.CharField(u"发起人", blank=True, max_length=50)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    run_reason = models.CharField("启动原因", blank=True, null=True, max_length=2500)


class StepRun(models.Model):
    step = models.ForeignKey(Step, blank=True, null=True)
    processrun = models.ForeignKey(ProcessRun, blank=True, null=True)
    starttime = models.DateTimeField(u"开始时间", blank=True, null=True)
    endtime = models.DateTimeField(u"结束时间", blank=True, null=True)
    operator = models.CharField(u"操作人", blank=True, null=True, max_length=50)
    parameter = models.CharField(u"运行参数", blank=True, null=True, max_length=5000)
    result = models.CharField(u"运行结果", blank=True, null=True, max_length=5000)
    explain = models.CharField(u"运行说明", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)


class ScriptRun(models.Model):
    script = models.ForeignKey(Script, blank=True, null=True)
    steprun = models.ForeignKey(StepRun, blank=True, null=True)
    starttime = models.DateTimeField(u"开始时间", blank=True, null=True)
    endtime = models.DateTimeField(u"结束时间", blank=True, null=True)
    operator = models.CharField(u"操作人", blank=True, null=True, max_length=50)
    result = models.CharField(u"运行结果", blank=True, null=True, max_length=5000)
    explain = models.CharField(u"运行说明", blank=True, null=True, max_length=5000)
    runlog = models.CharField(u"运行日志", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)


class ProcessTask(models.Model):
    processrun = models.ForeignKey(ProcessRun, blank=True, null=True)
    steprun = models.ForeignKey(StepRun, blank=True, null=True)
    starttime = models.DateTimeField(u"发送时间", blank=True, null=True)
    senduser = models.CharField(u"发送人", blank=True, null=True, max_length=50)
    receiveuser = models.CharField(u"接收人", blank=True, null=True, max_length=50)
    receiveauth = models.CharField(u"接收角色", blank=True, null=True, max_length=50)
    operator = models.CharField(u"操作人", blank=True, null=True, max_length=50)
    endtime = models.DateTimeField(u"处理时间", blank=True, null=True)
    type = models.CharField(u"任务类型", blank=True, null=True, max_length=20)
    content = models.CharField(u"任务内容", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    result = models.CharField(u"处理结果", blank=True, null=True, max_length=5000)
    explain = models.CharField(u"处理说明", blank=True, null=True, max_length=5000)
