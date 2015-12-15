# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GAReportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('for_date', models.DateField(null=True)),
                ('email_subject', models.CharField(max_length=1024, null=True)),
                ('from_address', models.CharField(max_length=1024, null=True)),
                ('csv_filename', models.CharField(max_length=1024, null=True)),
                ('ad_groups', models.CharField(max_length=128, null=True)),
                ('s3_key', models.CharField(max_length=1024, null=True)),
                ('visits_reported', models.IntegerField(null=True)),
                ('visits_imported', models.IntegerField(null=True)),
                ('multimatch', models.IntegerField(default=0)),
                ('multimatch_clicks', models.IntegerField(default=0)),
                ('nomatch', models.IntegerField(default=0)),
                ('state', models.IntegerField(default=1, choices=[(1, b'Received'), (4, b'Success'), (-1, b'Failed'), (3, b'EmptyReport'), (2, b'Parsed')])),
                ('errors', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RawGoalConversionStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('ad_group_id', models.IntegerField(default=0)),
                ('source_id', models.IntegerField(default=0, null=True)),
                ('url_raw', models.CharField(max_length=2048)),
                ('url_clean', models.CharField(max_length=2048)),
                ('device_type', models.CharField(max_length=64, null=True)),
                ('goal_name', models.CharField(max_length=127)),
                ('z1_adgid', models.CharField(max_length=32)),
                ('z1_msid', models.CharField(max_length=64)),
                ('conversions', models.IntegerField(default=0)),
                ('conversions_value_cc', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='RawPostclickStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField()),
                ('ad_group_id', models.IntegerField(default=0)),
                ('source_id', models.IntegerField(default=0, null=True)),
                ('url_raw', models.CharField(max_length=2048)),
                ('url_clean', models.CharField(max_length=2048)),
                ('device_type', models.CharField(max_length=64, null=True)),
                ('z1_adgid', models.CharField(max_length=32)),
                ('z1_msid', models.CharField(max_length=64)),
                ('visits', models.IntegerField(default=0)),
                ('new_visits', models.IntegerField(default=0)),
                ('bounced_visits', models.IntegerField(default=0)),
                ('pageviews', models.IntegerField(default=0)),
                ('duration', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ReportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('for_date', models.DateField(null=True)),
                ('email_subject', models.CharField(max_length=1024, null=True)),
                ('from_address', models.CharField(max_length=1024, null=True)),
                ('report_filename', models.CharField(max_length=1024, null=True)),
                ('visits_reported', models.IntegerField(null=True)),
                ('visits_imported', models.IntegerField(null=True)),
                ('s3_key', models.CharField(max_length=1024, null=True)),
                ('state', models.IntegerField(default=1, choices=[(1, b'Received'), (4, b'Success'), (-1, b'Failed'), (3, b'EmptyReport'), (2, b'Parsed')])),
                ('errors', models.TextField(null=True)),
            ],
        ),
    ]
