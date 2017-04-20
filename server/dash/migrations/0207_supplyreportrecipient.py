# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-20 07:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0206_auto_20170419_1449'),
        ('reports', '0010_auto_20170414_1449'),
    ]

    state_operations = [
        migrations.CreateModel(
            name='SupplyReportRecipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name=b'first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name=b'last name')),
                ('email', models.EmailField(max_length=255, verbose_name=b'email address')),
                ('custom_subject', models.CharField(blank=True, max_length=100)),
                ('publishers_report', models.BooleanField(default=False)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Source')),
            ],
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
        )
    ]
