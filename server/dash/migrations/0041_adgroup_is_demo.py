# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0040_auto_20141022_1127'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroup',
            name='is_demo',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
