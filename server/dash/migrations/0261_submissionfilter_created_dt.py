# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-12 15:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0260_auto_20171204_0844'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissionfilter',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name=b'Created at'),
            preserve_default=False,
        ),
    ]
