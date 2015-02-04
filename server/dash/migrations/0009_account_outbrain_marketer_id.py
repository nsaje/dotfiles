# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0008_auto_20150204_1622'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='outbrain_marketer_id',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
