# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0082_auto_20151103_0959'),
    ]

    operations = [
        migrations.AddField(
            model_name='publisherblacklist',
            name='status',
            field=models.IntegerField(default=2, choices=[(2, b'Blcklisted'), (1, b'Enabled'), (3, b'Pending')]),
        ),
    ]
