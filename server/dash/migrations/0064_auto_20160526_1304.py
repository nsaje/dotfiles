# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-26 13:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0063_facebookaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='image_crop',
            field=models.CharField(max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='contentadcandidate',
            name='image_status',
            field=models.IntegerField(choices=[(2, b'OK'), (3, b'Failed'), (1, b'Waiting')], default=1),
        ),
        migrations.AddField(
            model_name='contentadcandidate',
            name='url_status',
            field=models.IntegerField(choices=[(2, b'OK'), (3, b'Failed'), (1, b'Waiting')], default=1),
        ),
    ]
