# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0075_auto_20150916_1005'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversionGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(1, b'Conversion Pixel'), (3, b'Omniture'), (2, b'Google Analytics')])),
                ('name', models.CharField(max_length=100)),
                ('conversion_window', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('goal_id', models.CharField(max_length=100, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created on')),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('pixel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.ConversionPixel', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='changes_text',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='conversiongoal',
            unique_together=set([('campaign', 'type', 'goal_id'), ('campaign', 'pixel'), ('campaign', 'name')]),
        ),
    ]
