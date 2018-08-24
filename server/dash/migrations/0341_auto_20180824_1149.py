# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-24 11:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0340_merge_20180823_0908")]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="type",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, "Native Content Distribution"),
                    (2, "Native Video Advertising"),
                    (3, "Native Conversion Marketing"),
                    (4, "Native Mobile App Advertising"),
                ],
                default=1,
                null=True,
            ),
        )
    ]
