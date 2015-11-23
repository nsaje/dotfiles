# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0088_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='uses_credits',
            field=models.BooleanField(default=False, verbose_name=b'Uses credits and budgets accounting'),
        ),
    ]
