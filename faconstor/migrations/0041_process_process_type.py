# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-06-22 14:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0040_auto_20200619_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='process_type',
            field=models.CharField(blank=True, max_length=50, verbose_name='预案类型'),
        ),
    ]