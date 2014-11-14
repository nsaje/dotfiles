# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0044_auto_20141030_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='changes_text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
