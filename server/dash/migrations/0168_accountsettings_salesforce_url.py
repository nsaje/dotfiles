# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-07 08:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0167_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='salesforce_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
