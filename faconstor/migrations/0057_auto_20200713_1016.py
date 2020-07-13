# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-07-13 10:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0056_scriptrun_script'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scriptinstance',
            name='commv_interface',
        ),
        migrations.AddField(
            model_name='script',
            name='commv_interface',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='commvault接口类名'),
        ),
    ]