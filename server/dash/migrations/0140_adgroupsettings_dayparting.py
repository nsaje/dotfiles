# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-25 08:34
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0139_auto_20161021_1034'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='dayparting',
            field=jsonfield.fields.JSONField(blank=True, default=dict),
        ),
    ]
