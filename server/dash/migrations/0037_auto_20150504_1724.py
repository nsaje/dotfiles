# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_uploadbatch_num_errors'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='brand_name',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='uploadbatch',
            name='call_to_action',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='uploadbatch',
            name='description',
            field=models.CharField(default=b'', max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='uploadbatch',
            name='display_url',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
    ]
