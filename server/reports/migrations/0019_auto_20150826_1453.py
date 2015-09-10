# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_auto_20150826_1449'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contentadgoalconversionstats',
            name='conversions',
        ),
        migrations.RenameField('contentadgoalconversionstats', 'conversions_int', 'conversions')
    ]
