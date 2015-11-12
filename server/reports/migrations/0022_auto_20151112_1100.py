# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0085_account_uses_credits'),
        ('reports', '0021_auto_20150923_1124'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetDailyStatement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('spend', models.DecimalField(max_digits=14, decimal_places=4)),
                ('date', models.DateField()),
                ('dirty', models.BooleanField(default=False)),
                ('budget', models.ForeignKey(to='dash.BudgetLineItem')),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.AlterUniqueTogether(
            name='budgetdailystatement',
            unique_together=set([('budget', 'date')]),
        ),
    ]
