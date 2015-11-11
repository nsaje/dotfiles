# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0084_contentad_crop_areas'),
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
        migrations.AddField(
            model_name='account',
            name='uses_credits',
            field=models.BooleanField(default=False, verbose_name=b'Uses credits and budgets accounting'),
        ),
        migrations.AlterUniqueTogether(
            name='budgetdailystatement',
            unique_together=set([('budget', 'date')]),
        ),
    ]
