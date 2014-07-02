# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_auto_20140701_1555'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([(b'url', b'title')]),
        ),
    ]
