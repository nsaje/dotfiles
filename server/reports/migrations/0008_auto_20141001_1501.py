# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_auto_20140904_0648'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupGoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('goal_name', models.CharField(max_length=127)),
                ('conversions', models.IntegerField(default=0)),
                ('conversions_value_cc', models.IntegerField(default=0)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AdGroupStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('impressions', models.IntegerField(default=0)),
                ('clicks', models.IntegerField(default=0)),
                ('cost_cc', models.IntegerField(default=0)),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('duration', models.IntegerField(default=0)),
                ('has_traffic_metrics', models.IntegerField(default=0)),
                ('has_postclick_metrics', models.IntegerField(default=0)),
                ('has_conversion_metrics', models.IntegerField(default=0)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='adgroupstats',
            unique_together=set([('datetime', 'ad_group', 'source')]),
        ),
        migrations.AlterUniqueTogether(
            name='adgroupgoalconversionstats',
            unique_together=set([('datetime', 'ad_group', 'source', 'goal_name')]),
        ),
    ]
