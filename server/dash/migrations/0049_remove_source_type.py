# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0048_move_type_data_to_source_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='source',
            name='type',
        ),
    ]
