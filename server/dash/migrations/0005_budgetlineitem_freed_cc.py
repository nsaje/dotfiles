# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0004_auto_20151216_0950'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetlineitem',
            name='freed_cc',
            field=models.BigIntegerField(default=0),
        ),
    ]
