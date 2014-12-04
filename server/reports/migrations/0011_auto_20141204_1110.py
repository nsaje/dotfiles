# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_merge'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='articlestats',
            index_together=set([('ad_group', 'datetime')]),
        ),
    ]
