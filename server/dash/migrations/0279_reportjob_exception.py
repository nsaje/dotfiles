# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-13 12:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0278_auto_20180212_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportjob',
            name='exception',
            field=models.TextField(blank=True, null=True),
        ),
    ]
