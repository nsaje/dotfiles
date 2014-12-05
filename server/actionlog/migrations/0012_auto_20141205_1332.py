# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0011_merge'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='actionlog',
            index_together=set([('id', 'created_dt')]),
        ),
    ]
