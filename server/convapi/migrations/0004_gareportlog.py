# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0003_auto_20140929_1003'),
    ]

    operations = [
        migrations.CreateModel(
            name='GAReportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('for_date', models.DateField()),
                ('email_subject', models.CharField(max_length=1024, null=True)),
                ('csv_filename', models.CharField(max_length=1024, null=True)),
                ('ad_groups', models.CharField(max_length=128, null=True)),
                ('visits_reported', models.IntegerField(null=True)),
                ('visits_imported', models.IntegerField(null=True)),
                ('state', models.IntegerField(default=1, choices=[(1, b'Received'), (4, b'Success'), (-1, b'Failed'), (3, b'EmptyReport'), (2, b'Parsed')])),
                ('errors', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
