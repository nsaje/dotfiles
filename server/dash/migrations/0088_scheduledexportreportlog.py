# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0087_auto_20151111_1557'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledExportReportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('report_filename', models.CharField(max_length=1024, null=True)),
                ('state', models.IntegerField(default=-1, choices=[(-1, b'Failed'), (1, b'Success')])),
                ('errors', models.TextField(null=True)),
                ('report', models.ForeignKey(to='dash.ExportReport')),
                ('scheduled_report', models.ForeignKey(to='dash.ScheduledExportReport')),
            ],
        ),
    ]
