# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-01 12:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0160_auto_20170127_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publishergroup',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
