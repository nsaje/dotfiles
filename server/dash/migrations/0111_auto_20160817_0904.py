# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-17 09:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0110_scheduledexportreport_day_of_week'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rule',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(4, b'Not contains'), (3, b'Not starts with'), (2, b'Contains'), (1, b'Starts with')]),
        ),
    ]
