# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0007_gareportlog_from_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rawgoalconversionstats',
            name='z1_did',
        ),
        migrations.RemoveField(
            model_name='rawgoalconversionstats',
            name='z1_kid',
        ),
        migrations.RemoveField(
            model_name='rawgoalconversionstats',
            name='z1_tid',
        ),
        migrations.RemoveField(
            model_name='rawpostclickstats',
            name='z1_did',
        ),
        migrations.RemoveField(
            model_name='rawpostclickstats',
            name='z1_kid',
        ),
        migrations.RemoveField(
            model_name='rawpostclickstats',
            name='z1_tid',
        ),
    ]
