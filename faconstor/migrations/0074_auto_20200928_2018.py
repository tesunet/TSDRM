# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-09-28 20:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0073_processschedule_pro_ins'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='processinstance',
            name='process',
        ),
        migrations.RemoveField(
            model_name='processschedule',
            name='pro_ins',
        ),
        migrations.DeleteModel(
            name='ProcessInstance',
        ),
    ]
