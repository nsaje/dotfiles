# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0056_auto_20150630_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='tracker_urls',
            field=django.contrib.postgres.fields.ArrayField(null=True, base_field=models.CharField(max_length=2048), size=None),
        ),
    ]
