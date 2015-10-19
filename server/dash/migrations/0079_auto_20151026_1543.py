# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from decimal import Decimal
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0078_useractionlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BudgetLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount', models.IntegerField()),
                ('comment', models.CharField(max_length=256, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('campaign', models.ForeignKey(related_name='budgets', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreditHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', jsonfield.fields.JSONField()),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreditLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount', models.IntegerField()),
                ('license_fee', models.DecimalField(default=Decimal('0.2000'), max_digits=5, decimal_places=4)),
                ('status', models.IntegerField(default=2, choices=[(1, b'Signed'), (3, b'Canceled'), (2, b'Pending')])),
                ('comment', models.CharField(max_length=256, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('account', models.ForeignKey(related_name='credits', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Created by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='credithistory',
            name='credit',
            field=models.ForeignKey(related_name='history', to='dash.CreditLineItem'),
        ),
        migrations.AddField(
            model_name='budgetlineitem',
            name='credit',
            field=models.ForeignKey(related_name='budgets', on_delete=django.db.models.deletion.PROTECT, to='dash.CreditLineItem'),
        ),
        migrations.AddField(
            model_name='budgethistory',
            name='budget',
            field=models.ForeignKey(related_name='history', to='dash.BudgetLineItem'),
        ),
        migrations.AddField(
            model_name='budgethistory',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
