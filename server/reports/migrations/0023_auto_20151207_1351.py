# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0022_auto_20151120_1706'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetdailystatement',
            name='dirty',
        ),
        migrations.RemoveField(
            model_name='budgetdailystatement',
            name='spend',
        ),
        migrations.AddField(
            model_name='budgetdailystatement',
            name='data_spend_nano',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='budgetdailystatement',
            name='license_fee_nano',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='budgetdailystatement',
            name='media_spend_nano',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
    ]
