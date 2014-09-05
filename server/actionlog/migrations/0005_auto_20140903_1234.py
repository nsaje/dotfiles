# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0004_auto_20140814_1418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlogorder',
            name='order_type',
            field=models.IntegerField(choices=[(3, b'AdGroup Settings Update'), (1, b'Fetch all'), (6, b'Create campaign'), (2, b'Stop all'), (4, b'Fetch reports'), (5, b'Fetch status')]),
        ),
    ]
