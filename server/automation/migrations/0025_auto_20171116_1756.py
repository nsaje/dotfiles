# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-16 17:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0024_auto_20171116_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='realtimedatahistory',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name=b'Created at'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='realtimedatahistory',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
    ]
