# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0004_gareportlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gareportlog',
            name='for_date',
            field=models.DateField(null=True),
        ),
    ]
