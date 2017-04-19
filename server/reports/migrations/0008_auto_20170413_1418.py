# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-13 14:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0007_supplyreportrecipient_custom_subject'),
    ]

    database_operations = [
        migrations.AlterModelTable('BudgetDailyStatement', 'dash_budgetdailystatement')
    ]

    state_operations = [
        migrations.AlterUniqueTogether(
            name='budgetdailystatement',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='budgetdailystatement',
            name='budget',
        ),
        migrations.DeleteModel(
            name='BudgetDailyStatement',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations,
        )
    ]
