# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-20 15:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0223_auto_20170620_1103'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditlineitem',
            name='contract_id',
            field=models.IntegerField(blank=True, null=True, verbose_name=b'SalesForce Contract ID'),
        ),
        migrations.AddField(
            model_name='creditlineitem',
            name='part_id',
            field=models.IntegerField(blank=True, null=True, verbose_name=b'SalesForce Contract Part ID'),
        ),
    ]
