# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-10-09 10:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0077_remove_processrun_process'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='processschedule',
            name='process',
        ),
        migrations.RemoveField(
            model_name='scriptinstance',
            name='hosts_manage',
        ),
        migrations.RemoveField(
            model_name='scriptinstance',
            name='primary',
        ),
        migrations.RemoveField(
            model_name='scriptinstance',
            name='utils',
        ),
    ]