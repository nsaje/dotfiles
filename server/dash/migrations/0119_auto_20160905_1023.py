# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-05 10:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0118_auto_20160901_0844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exportreport',
            name='additional_fields',
            field=models.TextField(blank=True, null=True),
        ),
    ]
