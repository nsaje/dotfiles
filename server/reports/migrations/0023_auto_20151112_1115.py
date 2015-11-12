# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0022_auto_20151112_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetdailystatement',
            name='spend',
            field=models.DecimalField(max_digits=16, decimal_places=6),
        ),
    ]
