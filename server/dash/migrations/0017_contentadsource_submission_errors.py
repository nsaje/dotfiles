# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0016_auto_20150224_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentadsource',
            name='submission_errors',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
