# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-01 13:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0087_auto_20160630_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentad',
            name='label',
            field=models.CharField(default=b'', max_length=100),
        ),
    ]
