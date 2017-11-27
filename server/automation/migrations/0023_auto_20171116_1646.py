# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-16 16:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0251_auto_20171109_1150'),
        ('automation', '0022_auto_20170921_1000'),
    ]

    operations = [
        migrations.CreateModel(
            name='RealTimeDataHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('etfm_spend', models.DecimalField(decimal_places=4, max_digits=14)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dash.AdGroup')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dash.Source')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='realtimedatahistory',
            unique_together=set([('ad_group', 'source', 'date')]),
        ),
    ]
