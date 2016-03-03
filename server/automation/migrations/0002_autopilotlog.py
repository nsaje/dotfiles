# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20160201_1505'),
        ('automation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutopilotLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('yesterdays_clicks', models.IntegerField(null=True)),
                ('yesterdays_spend_cc', models.DecimalField(decimal_places=4, default=0, max_digits=10, blank=True, null=True, verbose_name=b"Yesterday's spend")),
                ('previous_cpc_cc', models.DecimalField(null=True, verbose_name=b'Previous CPC', max_digits=10, decimal_places=4, blank=True)),
                ('new_cpc_cc', models.DecimalField(null=True, verbose_name=b'New CPC', max_digits=10, decimal_places=4, blank=True)),
                ('previous_daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Previous daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('new_daily_budget_cc', models.DecimalField(null=True, verbose_name=b'New daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('comments', models.CharField(max_length=1024, null=True, blank=True)),
                ('ad_group', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('ad_group_source', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource')),
            ],
        ),
    ]
