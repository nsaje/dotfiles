# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0001_initial'),
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
        ),
        migrations.CreateModel(
            name='AdGroupStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('impressions', models.IntegerField(default=0)),
                ('clicks', models.IntegerField(default=0)),
                ('cost_cc', models.IntegerField(default=0)),
                ('data_cost_cc', models.IntegerField(default=0)),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('duration', models.IntegerField(default=0)),
                ('has_traffic_metrics', models.IntegerField(default=0)),
                ('has_postclick_metrics', models.IntegerField(default=0)),
                ('has_conversion_metrics', models.IntegerField(default=0)),
                ('datetime', models.DateTimeField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='ArticleStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('impressions', models.IntegerField(default=0)),
                ('clicks', models.IntegerField(default=0)),
                ('cost_cc', models.IntegerField(default=0)),
                ('data_cost_cc', models.IntegerField(default=0)),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('duration', models.IntegerField(default=0)),
                ('has_traffic_metrics', models.IntegerField(default=0)),
                ('has_postclick_metrics', models.IntegerField(default=0)),
                ('has_conversion_metrics', models.IntegerField(default=0)),
                ('datetime', models.DateTimeField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('article', models.ForeignKey(to='dash.Article', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'permissions': (),
            },
        ),
        migrations.CreateModel(
            name='BudgetDailyStatement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('media_spend_nano', models.BigIntegerField()),
                ('data_spend_nano', models.BigIntegerField()),
                ('license_fee_nano', models.BigIntegerField()),
                ('budget', models.ForeignKey(to='dash.BudgetLineItem')),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='ContentAdGoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(verbose_name=b'Report date')),
                ('goal_type', models.SlugField(default=b'ga', max_length=15, choices=[(b'ga', b'Google Analytics'), (b'omniture', b'Adobe Analytics')])),
                ('goal_name', models.CharField(max_length=256, editable=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('conversions', models.IntegerField(null=True)),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='ContentAdPostclickStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name=b'Report date')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('visits', models.IntegerField(null=True)),
                ('new_visits', models.IntegerField(null=True)),
                ('bounced_visits', models.IntegerField(null=True)),
                ('pageviews', models.IntegerField(null=True)),
                ('total_time_on_site', models.IntegerField(null=True)),
                ('content_ad', models.ForeignKey(to='dash.ContentAd', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
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
        ),
        migrations.CreateModel(
            name='GoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('goal_name', models.CharField(max_length=127)),
                ('conversions', models.IntegerField(default=0)),
                ('conversions_value_cc', models.IntegerField(default=0)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT)),
                ('article', models.ForeignKey(to='dash.Article', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='SupplyReportRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=30, verbose_name=b'first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name=b'last name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'email address')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='goalconversionstats',
            unique_together=set([('datetime', 'ad_group', 'article', 'source', 'goal_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentadstats',
            unique_together=set([('date', 'content_ad_source')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentadpostclickstats',
            unique_together=set([('date', 'content_ad', 'source')]),
        ),
        migrations.AlterUniqueTogether(
            name='contentadgoalconversionstats',
            unique_together=set([('date', 'content_ad', 'source', 'goal_type', 'goal_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='budgetdailystatement',
            unique_together=set([('budget', 'date')]),
        ),
        migrations.AlterUniqueTogether(
            name='articlestats',
            unique_together=set([('datetime', 'ad_group', 'article', 'source')]),
        ),
        migrations.AlterIndexTogether(
            name='articlestats',
            index_together=set([('ad_group', 'datetime')]),
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
