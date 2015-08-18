# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_trackingpixel'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversionPixel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.TextField()),
                ('status', models.IntegerField(default=1, choices=[(1, b'Not used'), (2, b'Inactive'), (3, b'Active')])),
                ('last_verified_dt', models.DateTimeField(verbose_name=b'Last verified on')),
                ('archived', models.BooleanField(default=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created on')),
                ('account', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
            ],
        ),
        migrations.RemoveField(
            model_name='trackingpixel',
            name='account',
        ),
        migrations.DeleteModel(
            name='TrackingPixel',
        ),
    ]
