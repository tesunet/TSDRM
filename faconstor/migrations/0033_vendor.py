# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-06-17 13:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0032_auto_20191011_2106'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default='', verbose_name='内容')),
            ],
        ),
    ]
