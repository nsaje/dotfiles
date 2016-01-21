# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0014_auto_20160121_1712'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaigngoal',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='campaigngoal',
            name='created_dt',
            field=models.DateTimeField(default=datetime.date(2016, 1, 21), verbose_name=b'Created at', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campaigngoalvalue',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='campaigngoalvalue',
            name='created_dt',
            field=models.DateTimeField(default=datetime.date(2016, 1, 21), verbose_name=b'Created at', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='campaigngoal',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='campaigngoalvalue',
            name='campaign_goal',
            field=models.ForeignKey(to='dash.CampaignGoal', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
