# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-27 09:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0140_adgroupsettings_dayparting'),
    ]

    operations = [
        migrations.AddField(
            model_name='exportreport',
            name='include_missing',
            field=models.BooleanField(default=False),
        ),
    ]
