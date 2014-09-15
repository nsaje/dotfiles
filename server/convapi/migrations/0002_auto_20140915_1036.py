# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rawgoalconversionstats',
            unique_together=None,
        ),
        migrations.AlterUniqueTogether(
            name='rawpostclickstats',
            unique_together=None,
        ),
    ]
