# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0015_auto_20160121_1741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaigngoal',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaigngoalvalue',
            name='campaign_goal',
            field=models.ForeignKey(to='dash.CampaignGoal'),
        ),
    ]
