# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_conversionpixel'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='conversionpixel',
            unique_together=set([('slug', 'account')]),
        ),
    ]
