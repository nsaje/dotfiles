# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-18 15:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0241_merge_20170913_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentad',
            name='display_url',
            field=models.CharField(blank=True, default=b'', max_length=35),
        ),
    ]
