# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0023_auto_20151207_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetdailystatement',
            name='budget',
            field=models.ForeignKey(related_name='statements', to='dash.BudgetLineItem'),
        ),
    ]
