# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0054_contentad_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='batch_size',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='uploadbatch',
            name='processed_content_ads',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
