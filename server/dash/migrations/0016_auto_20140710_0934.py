# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0015_network_maintenance'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([(b'ad_group', b'url', b'title')]),
        ),
    ]
