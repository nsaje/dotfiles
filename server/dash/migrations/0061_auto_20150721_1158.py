# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0060_source_actions_data_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourcetype',
            name='available_actions',
        ),
        migrations.DeleteModel(
            name='SourceAction',
        ),
    ]
