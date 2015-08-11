# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0058_auto_20150707_0945'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='available_actions_new',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.PositiveSmallIntegerField(), blank=True),
        ),
    ]
