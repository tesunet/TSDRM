# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-09-22 14:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0066_process_primary'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='hosts_config',
            field=models.TextField(default='<root></root>', null=True, verbose_name='关联主机'),
        ),
        migrations.AlterField(
            model_name='processschedule',
            name='name',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='流程计划名称'),
        ),
        migrations.AlterField(
            model_name='processschedule',
            name='remark',
            field=models.TextField(blank=True, null=True, verbose_name='计划说明'),
        ),
        migrations.AlterField(
            model_name='processschedule',
            name='state',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='状态'),
        ),
    ]
