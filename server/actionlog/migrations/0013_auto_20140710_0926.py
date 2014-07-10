# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0012_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlogorder',
            name='order_type',
            field=models.IntegerField(choices=[(3, b'AdGroup Settings Update'), (1, b'Fetch all'), (2, b'Stop all')]),
        ),
    ]
