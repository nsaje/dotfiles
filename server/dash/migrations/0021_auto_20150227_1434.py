# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20150227_1416'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adgroupsettings',
            old_name='short_name',
            new_name='display_url',
        ),
    ]
