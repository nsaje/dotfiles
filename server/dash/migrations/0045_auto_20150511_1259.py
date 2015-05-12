# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import dash.constants

def forwards_code(apps, schema_editor):
    SourceAction = apps.get_model('dash', 'SourceAction')
    for source_action in dash.constants.SourceAction.get_all():
        try:
            SourceAction.objects.get(action=source_action)
        except SourceAction.DoesNotExist:
            SourceAction.objects.create(action=source_action)


def reverse_code(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0044_auto_20150511_1255'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards_code,
            reverse_code=reverse_code
        )
    ]
