# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0088_accountsettings_allowed_sources'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='released',
            field=models.BooleanField(default=True),
        ),
    ]
