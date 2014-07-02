# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0010_auto_20140701_0912'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'get_latest_by': b'created_dt'},
        ),
    ]
