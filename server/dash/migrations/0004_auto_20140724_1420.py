# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0003_auto_20140722_1710'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroup',
            options={'permissions': ((b'chart_legend_view', b'Can view chart legend in Media Sources tab.'),)},
        ),
    ]
