# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_auto_20150909_1206'),
        ('automation', '0007_proposedadgroupsourcebidcpc'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutopilotAdGroupSourceBidCpcLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('yesterdays_spend_cc', models.DecimalField(decimal_places=4, default=0, max_digits=10, blank=True, null=True, verbose_name=b"Yesterday's spend")),
                ('previous_cpc_cc', models.DecimalField(null=True, verbose_name=b'Previous CPC', max_digits=10, decimal_places=4, blank=True)),
                ('new_cpc_cc', models.DecimalField(null=True, verbose_name=b'New CPC', max_digits=10, decimal_places=4, blank=True)),
                ('current_daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('ad_group_source', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource')),
                ('campaign', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
            ],
        ),
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='ad_group',
        ),
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='ad_group_source',
        ),
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='campaign',
        ),
        migrations.DeleteModel(
            name='ProposedAdGroupSourceBidCpc',
        ),
    ]
