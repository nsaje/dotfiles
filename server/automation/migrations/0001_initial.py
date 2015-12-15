# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutopilotAdGroupSourceBidCpcLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('yesterdays_clicks', models.IntegerField(null=True)),
                ('yesterdays_spend_cc', models.DecimalField(decimal_places=4, default=0, max_digits=10, blank=True, null=True, verbose_name=b"Yesterday's spend")),
                ('previous_cpc_cc', models.DecimalField(null=True, verbose_name=b'Previous CPC', max_digits=10, decimal_places=4, blank=True)),
                ('new_cpc_cc', models.DecimalField(null=True, verbose_name=b'New CPC', max_digits=10, decimal_places=4, blank=True)),
                ('current_daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('comments', models.CharField(max_length=1024, null=True, blank=True)),
                ('ad_group', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('ad_group_source', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource')),
                ('campaign', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
            ],
        ),
        migrations.CreateModel(
            name='CampaignBudgetDepletionNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('available_budget', models.DecimalField(decimal_places=4, default=0, max_digits=20, blank=True, null=True, verbose_name=b'Budget available at creation')),
                ('yesterdays_spend', models.DecimalField(decimal_places=4, default=0, max_digits=20, blank=True, null=True, verbose_name=b"Campaign's yesterday's spend")),
                ('stopped', models.BooleanField(default=False)),
                ('account_manager', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('campaign', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
            ],
        ),
    ]
