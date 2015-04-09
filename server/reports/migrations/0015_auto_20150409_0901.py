# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0028_auto_20150331_1354'),
        ('reports', '0014_auto_20150326_1532'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentAdStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('impressions', models.IntegerField(null=True)),
                ('clicks', models.IntegerField(null=True)),
                ('cost_cc', models.IntegerField(null=True)),
                ('data_cost_cc', models.IntegerField(null=True)),
                ('date', models.DateField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
                ('content_ad_source', models.ForeignKey(to='dash.ContentAdSource', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='contentadstats',
            unique_together=set([('date', 'content_ad_source')]),
        ),
    ]
