# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0014_actionlog_content_ad_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='state',
            field=models.IntegerField(default=1, db_index=True, choices=[(-1, b'Failed'), (1, b'Waiting'), (2, b'Success'), (3, b'Aborted'), (4, b'Delayed')]),
        ),
    ]
