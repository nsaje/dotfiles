# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-02 12:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0162_customhack'),
    ]

    operations = [
        migrations.AddField(
            model_name='customhack',
            name='removed_dt',
            field=models.DateTimeField(blank=True, null=True, verbose_name=b'Removed at'),
        ),
    ]
