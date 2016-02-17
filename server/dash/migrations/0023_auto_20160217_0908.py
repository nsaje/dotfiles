# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0022_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='cancelled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uploadbatch',
            name='propagated_content_ads',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
