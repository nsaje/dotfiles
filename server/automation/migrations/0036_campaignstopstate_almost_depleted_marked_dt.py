# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-12 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0035_auto_20180302_1030'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignstopstate',
            name='almost_depleted_marked_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
