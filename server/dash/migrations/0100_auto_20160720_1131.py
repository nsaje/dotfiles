# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-20 11:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0099_budgetlineitem_margin'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversionpixel',
            name='name',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
    ]
