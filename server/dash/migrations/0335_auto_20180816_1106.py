# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-16 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0334_auto_20180816_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaignsettings',
            name='type',
            field=models.IntegerField(choices=[(1, 'Content'), (2, 'Video')], default=1, null=True),
        ),
    ]
