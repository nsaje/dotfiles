# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0010_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actionlog',
            options={'ordering': (b'-created_dt',), 'permissions': ((b'manual_view', b'Can view manual ActionLog actions'), (b'manual_acknowledge', b'Can acknowledge manual ActionLog actions'))},
        ),
        migrations.AlterField(
            model_name='actionlogorder',
            name='order_type',
            field=models.IntegerField(choices=[(2, b'AdGroup Settings Update'), (1, b'Fetch all')]),
        ),
    ]
