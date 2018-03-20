# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-16 11:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0282_allrtbadgroupsource'),
        ('automation', '0036_campaignstopstate_almost_depleted_marked_dt'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autopilotadgroupsourcebidcpclog',
            name='ad_group',
        ),
        migrations.RemoveField(
            model_name='autopilotadgroupsourcebidcpclog',
            name='ad_group_source',
        ),
        migrations.RemoveField(
            model_name='autopilotadgroupsourcebidcpclog',
            name='campaign',
        ),
        migrations.AddField(
            model_name='autopilotlog',
            name='campaign',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='dash.Campaign'),
        ),
        migrations.DeleteModel(
            name='AutopilotAdGroupSourceBidCpcLog',
        ),
    ]
