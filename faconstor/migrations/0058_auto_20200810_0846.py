# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-08-10 08:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0057_auto_20200713_1016'),
    ]

    operations = [
        migrations.CreateModel(
            name='CvClient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.IntegerField(blank=True, null=True, verbose_name='源端client_id')),
                ('client_name', models.CharField(blank=True, max_length=128, null=True, verbose_name='源端client_name')),
                ('type', models.TextField(blank=True, null=True, verbose_name='客户端类型')),
                ('agentType', models.TextField(blank=True, null=True, verbose_name='应用类型')),
                ('instanceName', models.TextField(blank=True, null=True, verbose_name='实例名')),
                ('info', models.TextField(blank=True, null=True, verbose_name='客户端相关信息')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sourceclient', to='faconstor.CvClient', verbose_name='默认关联终端')),
            ],
        ),
        migrations.RemoveField(
            model_name='scriptinstance',
            name='origin',
        ),
        migrations.AddField(
            model_name='hostsmanage',
            name='nodetype',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='节点类型'),
        ),
        migrations.AddField(
            model_name='hostsmanage',
            name='pnode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='faconstor.HostsManage', verbose_name='父节点'),
        ),
        migrations.AddField(
            model_name='hostsmanage',
            name='remark',
            field=models.TextField(default='', null=True, verbose_name='节点/客户端说明'),
        ),
        migrations.AddField(
            model_name='hostsmanage',
            name='sort',
            field=models.IntegerField(blank=True, null=True, verbose_name='排序'),
        ),
        migrations.AddField(
            model_name='cvclient',
            name='hostsmanage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.HostsManage', verbose_name='客户端'),
        ),
        migrations.AddField(
            model_name='cvclient',
            name='utils',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.UtilsManage', verbose_name='关联工具'),
        ),
        migrations.AddField(
            model_name='scriptinstance',
            name='primary',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.CvClient', verbose_name='源端客户端'),
        ),
    ]
