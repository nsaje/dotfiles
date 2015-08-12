# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0064_remove_sourcetype_available_actions_new'),
        ('reports', '0016_supplyreportrecipient'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentAdPostclickStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Report date')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('total_time_on_site', models.IntegerField(default=0)),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='contentadpostclickstats',
            unique_together=set([('date', 'content_ad', 'source')]),
        ),
    ]
