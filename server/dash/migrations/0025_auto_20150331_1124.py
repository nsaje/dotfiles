# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):
    dependencies = [
        ('dash', '0024_auto_20150323_1127'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contentad',
            options={'get_latest_by': 'created_dt'},
        ),
        migrations.AddField(
            model_name='contentad',
            name='ad_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, null=True, to='dash.AdGroup'),
        ),
        migrations.AddField(
            model_name='contentad',
            name='created_dt',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 31, 11, 24, 4, 202821), verbose_name=b'Created at', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contentad',
            name='title',
            field=models.CharField(default='title', max_length=256, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contentad',
            name='url',
            field=models.CharField(default='example.com', max_length=2048, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contentad',
            name='batch',
            field=models.ForeignKey(to='dash.UploadBatch', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
