# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-07-10 13:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0055_remove_scriptrun_script'),
    ]

    operations = [
        migrations.AddField(
            model_name='scriptrun',
            name='script',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.ScriptInstance'),
        ),
    ]