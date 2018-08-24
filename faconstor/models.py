# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User

class Fun(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField(u"功能名称",  max_length=100)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    type = models.CharField(u"类型", blank=True,null=True, max_length=20)
    url = models.CharField(u"地址", blank=True,null=True, max_length=500)
    icon = models.CharField(u"图标",blank=True,null=True, max_length=100)


class Group(models.Model):
    name = models.CharField(u"组名", blank=True, null=True,max_length=50)
    fun = models.ManyToManyField(Fun)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)


class UserInfo(models.Model):
    user = models.OneToOneField(User, blank=True, null=True,)
    userGUID = models.CharField(u"GUID", null=True, max_length=50)
    fullname = models.CharField(u"姓名",blank=True,max_length=50)
    phone = models.CharField(u"电话", blank=True, null=True,max_length=50)
    group = models.ManyToManyField(Group)
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    type = models.CharField(u"类型", blank=True, null=True, max_length=20)
    state = models.CharField(u"状态", blank=True,null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    company = models.CharField(u"公司", blank=True, null=True,max_length=100)
    tell = models.CharField(u"电话", blank=True, null=True,max_length=50)
    forgetpassword = models.CharField(u"修改密码地址", blank=True, null=True,max_length=50)


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


class ProcessRun(models.Model):
    process = models.ForeignKey(Process)
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
