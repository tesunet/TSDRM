# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-09-21 10:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0028_processtask_walkthrough'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processtask',
            name='walkthrough',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.Walkthrough'),
        ),
    ]
