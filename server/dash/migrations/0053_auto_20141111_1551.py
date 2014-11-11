# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0052_sourcetype_available_actions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sourcetype',
            options={'verbose_name': 'Source Type', 'verbose_name_plural': 'Source Types'},
        ),
    ]
