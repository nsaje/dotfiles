# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0044_auto_20141030_1303'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupSourceState',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
                ('ad_group_source', models.ForeignKey(related_name=b'states', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'get_latest_by': 'created_dt',
            },
            bases=(models.Model,),
        ),
    ]
