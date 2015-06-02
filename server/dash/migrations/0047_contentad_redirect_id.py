# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0046_auto_20150523_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='redirect_id',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
