# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0053_auto_20150603_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
