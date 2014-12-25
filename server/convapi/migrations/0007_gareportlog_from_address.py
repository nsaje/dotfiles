# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0006_auto_20141204_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='gareportlog',
            name='from_address',
            field=models.CharField(max_length=1024, null=True),
            preserve_default=True,
        ),
    ]
