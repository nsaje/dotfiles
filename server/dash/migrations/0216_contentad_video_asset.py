# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-06 09:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0215_contentadcandidate_video_asset'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='video_asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dash.VideoAsset'),
        ),
    ]
