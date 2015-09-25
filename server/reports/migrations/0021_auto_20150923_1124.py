# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0020_auto_20150908_1655'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlestats',
            options={'permissions': ()},
        ),
    ]
