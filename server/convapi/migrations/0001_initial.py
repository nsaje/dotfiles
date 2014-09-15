# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RawGoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('ad_group_id', models.IntegerField(default=0)),
                ('source_id', models.IntegerField(default=0, null=True)),
                ('url_raw', models.CharField(max_length=2048)),
                ('url_clean', models.CharField(max_length=2048)),
                ('device_type', models.CharField(max_length=64)),
                ('goal_name', models.CharField(max_length=127)),
                ('z1_adgid', models.CharField(max_length=32)),
                ('z1_msid', models.CharField(max_length=64)),
                ('z1_did', models.CharField(max_length=64, null=True)),
                ('z1_kid', models.CharField(max_length=64, null=True)),
                ('z1_tid', models.CharField(max_length=64, null=True)),
                ('conversions', models.IntegerField(default=0)),
                ('conversions_value_cc', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RawPostclickStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('ad_group_id', models.IntegerField(default=0)),
                ('source_id', models.IntegerField(default=0, null=True)),
                ('url_raw', models.CharField(max_length=2048)),
                ('url_clean', models.CharField(max_length=2048)),
                ('device_type', models.CharField(max_length=64)),
                ('z1_adgid', models.CharField(max_length=32)),
                ('z1_msid', models.CharField(max_length=64)),
                ('z1_did', models.CharField(max_length=64, null=True)),
                ('z1_kid', models.CharField(max_length=64, null=True)),
                ('z1_tid', models.CharField(max_length=64, null=True)),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('duration', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='rawpostclickstats',
            unique_together=set([('datetime', 'url_raw')]),
        ),
        migrations.AlterUniqueTogether(
            name='rawgoalconversionstats',
            unique_together=set([('datetime', 'url_raw', 'goal_name')]),
        ),
    ]
