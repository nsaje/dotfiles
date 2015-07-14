# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0057_contentad_tracker_urls'),
        ('reports', '0015_auto_20150409_0901'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplyReportRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=30, verbose_name=b'first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name=b'last name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'email address')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
    ]
