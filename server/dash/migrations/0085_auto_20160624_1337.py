# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-24 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0084_auto_20160624_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentadcandidate',
            name='primary_tracker_url',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='contentadcandidate',
            name='secondary_tracker_url',
            field=models.TextField(null=True),
        ),
    ]
