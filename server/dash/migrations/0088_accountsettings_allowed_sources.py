# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0087_auto_20151111_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='allowed_sources',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.IntegerField(), size=None),
        ),
    ]
