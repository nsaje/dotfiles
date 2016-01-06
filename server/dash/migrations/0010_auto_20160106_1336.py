# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_campaignsettings_campaign_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='GAAnalyticsAccount',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('ga_account_id', models.CharField(max_length=127)),
                ('ga_web_property_id', models.CharField(max_length=127)),
                ('account', models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='ga_tracking_type',
            field=models.IntegerField(default=1, choices=[(2, b'API'), (1, b'Email')]),
        ),
    ]
