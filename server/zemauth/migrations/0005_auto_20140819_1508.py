# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0004_internalgroup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='internalgroup',
            name='group',
            field=models.ForeignKey(to='auth.Group', on_delete=django.db.models.deletion.PROTECT, unique=True),
        ),
    ]
