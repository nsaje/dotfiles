# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0054_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='changes_text',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
