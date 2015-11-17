# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0082_auto_20151103_0959'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledReport',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=1, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('sending_frequency', models.IntegerField(default=1, choices=[(3, b'Monthly'), (1, b'Daily'), (2, b'Weekly')])),
                ('order_by', models.CharField(max_length=20, null=True, blank=True)),
                ('additional_fields', models.CharField(max_length=500, null=True, blank=True)),
                ('filtered_sources', models.CharField(max_length=500, null=True, blank=True)),
                ('granularity', models.IntegerField(default=1, choices=[(6, b'Content Ad'), (4, b'Campaign'), (3, b'Account'), (5, b'Ad Group'), (2, b'All Accounts'), (1, b'View')])),
                ('breakdown_by_day', models.BooleanField(default=False)),
                ('breakdown_by_source', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Account', null=True)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroup', null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Campaign', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledReportRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('report', models.ForeignKey(related_name='recipients', to='dash.ScheduledReport')),
            ],
        ),
    ]
