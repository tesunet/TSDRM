# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-09-21 09:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('faconstor', '0027_processrun_walkthroughstate'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtask',
            name='walkthrough',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='faconstor.Walkthrough'),
        ),
    ]