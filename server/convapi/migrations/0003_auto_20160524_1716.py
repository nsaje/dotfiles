# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-24 17:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0002_auto_20151221_1558'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GAReportLog',
        ),
        migrations.DeleteModel(
            name='RawGoalConversionStats',
        ),
        migrations.DeleteModel(
            name='RawPostclickStats',
        ),
        migrations.DeleteModel(
            name='ReportLog',
        ),
    ]
