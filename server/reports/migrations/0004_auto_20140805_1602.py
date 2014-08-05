# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_auto_20140801_1326'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlestats',
            options={'permissions': ((b'yesterday_spend_view', b'Can view yesterday spend column.'), (b'fewer_daterange_options', b'Has fewer options available in daterange picker.'))},
        ),
    ]
