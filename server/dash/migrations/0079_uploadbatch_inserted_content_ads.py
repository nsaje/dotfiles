# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0078_useractionlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='inserted_content_ads',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
