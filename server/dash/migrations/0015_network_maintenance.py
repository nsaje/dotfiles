# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0014_auto_20140702_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='maintenance',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
