# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0072_auto_20150911_1004'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversionGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('name', models.CharField(max_length=256)),
                ('window', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('goal_id', models.CharField(max_length=256, null=True, blank=True)),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('pixel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.ConversionPixel', null=True)),
            ],
        ),
    ]
