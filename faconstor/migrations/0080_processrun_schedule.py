# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-10-14 15:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0079_processinstance_pnode'),
    ]

    operations = [
        migrations.AddField(
            model_name='processrun',
            name='schedule',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.ProcessSchedule', verbose_name='计划流程'),
        ),
    ]
