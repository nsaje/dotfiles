# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-23 09:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0314_auto_20180511_0913'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroup',
            name='outbrain_ad_review',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='ad_review_only',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='contentad',
            name='outbrain_ad_review',
            field=models.NullBooleanField(default=None),
        ),
    ]
