# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_remove_defaultsourcesettings_auto_add'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveSmallIntegerField(default=1, choices=[(1, b'time on site in seconds'), (6, b'$CPM'), (4, b'$CPA'), (5, b'$CPC'), (3, b'pages per session'), (2, b'max bounce rate %')])),
                ('campaign', models.ForeignKey(to='dash.Campaign')),
            ],
        ),
        migrations.CreateModel(
            name='CampaignGoalValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.DecimalField(max_digits=15, decimal_places=5)),
                ('campaign_goal', models.ForeignKey(to='dash.CampaignGoal')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='campaigngoal',
            unique_together=set([('campaign', 'type')]),
        ),
    ]
