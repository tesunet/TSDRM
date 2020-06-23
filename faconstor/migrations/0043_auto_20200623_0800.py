# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-06-23 08:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0042_remove_process_process_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='processrun',
            name='browse_job_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='指点时间点的备份任务ID'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='copy_priority',
            field=models.IntegerField(blank=True, default=1, null=True, verbose_name='优先拷贝顺序'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='curSCN',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='当前备份nextSCN-1'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='data_path',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='数据重定向路径'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='db_open',
            field=models.IntegerField(default=1, null=True, verbose_name='是否打开数据库'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='log_restore',
            field=models.IntegerField(default=1, null=True, verbose_name='是否回滚日志'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='origin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.Origin', verbose_name='源客户端'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='recover_end_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='恢复结束时间'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='recover_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='指定恢复时间点'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='rto',
            field=models.IntegerField(default=0, null=True, verbose_name='流程RTO'),
        ),
        migrations.AddField(
            model_name='processrun',
            name='target',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.Target', verbose_name='oracle恢复流程指定目标客户端'),
        ),
    ]