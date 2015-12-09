# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0095_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accountsettings',
            name='allowed_sources',
        ),
    ]
