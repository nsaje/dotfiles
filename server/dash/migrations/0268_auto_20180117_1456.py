# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-17 14:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0267_auto_20180115_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='whitelabel',
            field=models.CharField(blank=True, choices=[(b'mediamond', b'Mediamond'), (b'adtechnacity', b'Adtechnacity'), (b'newscorp', b'Newscorp'), (b'burda', b'Burda'), (b'greenpark', b'Green Park Content')], max_length=255),
        ),
    ]
