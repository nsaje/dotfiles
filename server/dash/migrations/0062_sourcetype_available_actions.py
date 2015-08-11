# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0061_auto_20150721_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='available_actions',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.PositiveSmallIntegerField(), blank=True),
        ),
    ]
