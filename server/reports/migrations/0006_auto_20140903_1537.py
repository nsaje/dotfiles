# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20140808_1646'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('goal_name', models.CharField(max_length=127)),
                ('conversions', models.IntegerField(default=0)),
                ('conversions_value_cc', models.IntegerField(default=0)),
                ('has_conversion_metrics', models.IntegerField(default=0)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('article', models.ForeignKey(to='dash.Article', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='goalconversionstats',
            unique_together=set([(b'datetime', b'ad_group', b'article', b'source', b'goal_name')]),
        ),
        migrations.AddField(
            model_name='articlestats',
            name='bounced_visits',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='duration',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='has_postclick_metrics',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='has_traffic_metrics',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='new_visits',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='pageviews',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='visits',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
