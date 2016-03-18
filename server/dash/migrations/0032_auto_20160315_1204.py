# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0031_auto_20160314_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaigngoal',
            name='conversion_goal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.ConversionGoal', null=True),
        ),
        migrations.AddField(
            model_name='campaigngoal',
            name='primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='campaigngoalvalue',
            name='campaign_goal',
            field=models.ForeignKey(related_name='values', to='dash.CampaignGoal'),
        ),
        migrations.AlterUniqueTogether(
            name='campaigngoal',
            unique_together=set([('campaign', 'type', 'conversion_goal')]),
        ),
    ]
