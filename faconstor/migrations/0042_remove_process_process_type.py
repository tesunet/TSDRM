# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-06-22 16:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0041_process_process_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='process',
            name='process_type',
        ),
    ]