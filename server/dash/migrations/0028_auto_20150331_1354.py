# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0027_auto_20150331_1220'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('ad_group', 'url', 'title')]),
        ),
    ]
