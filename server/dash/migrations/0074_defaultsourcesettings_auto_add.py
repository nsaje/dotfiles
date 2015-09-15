# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0073_auto_20150915_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='auto_add',
            field=models.BooleanField(default=False, verbose_name=b'Auto add to ad group at creation'),
        ),
    ]
