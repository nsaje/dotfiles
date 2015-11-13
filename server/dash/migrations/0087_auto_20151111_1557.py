# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0086_auto_20151109_1056'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportReport',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('granularity', models.IntegerField(default=5, choices=[(5, b'Content Ad'), (4, b'Ad Group'), (3, b'Campaign'), (1, b'All Accounts'), (2, b'Account')])),
                ('breakdown_by_day', models.BooleanField(default=False)),
                ('breakdown_by_source', models.BooleanField(default=False)),
                ('order_by', models.CharField(max_length=20, null=True, blank=True)),
                ('additional_fields', models.CharField(max_length=500, null=True, blank=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Account', null=True)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroup', null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Campaign', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('filtered_sources', models.ManyToManyField(to='dash.Source')),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledExportReport',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('state', models.IntegerField(default=1, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('sending_frequency', models.IntegerField(default=1, choices=[(3, b'Monthly'), (1, b'Daily'), (2, b'Weekly')])),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(related_name='scheduled_reports', to='dash.ExportReport')),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledExportReportRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('scheduled_report', models.ForeignKey(related_name='recipients', to='dash.ScheduledExportReport')),
            ],
        ),
        migrations.RemoveField(
            model_name='scheduledreport',
            name='account',
        ),
        migrations.RemoveField(
            model_name='scheduledreport',
            name='ad_group',
        ),
        migrations.RemoveField(
            model_name='scheduledreport',
            name='campaign',
        ),
        migrations.RemoveField(
            model_name='scheduledreport',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='scheduledreport',
            name='filtered_sources',
        ),
        migrations.AlterUniqueTogether(
            name='scheduledreportrecipient',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='scheduledreportrecipient',
            name='report',
        ),
        migrations.DeleteModel(
            name='ScheduledReport',
        ),
        migrations.DeleteModel(
            name='ScheduledReportRecipient',
        ),
        migrations.AlterUniqueTogether(
            name='scheduledexportreportrecipient',
            unique_together=set([('scheduled_report', 'email')]),
        ),
    ]
