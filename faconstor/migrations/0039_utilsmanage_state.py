# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-06-18 13:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0038_auto_20200618_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilsmanage',
            name='state',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='状态'),
        ),
    ]
