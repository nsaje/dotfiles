# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


import dash.constants


# custom code to get source actions up to date in db
def source_action_initial_data_forwards_code(apps, schema_editor):
    SourceAction = apps.get_model('dash', 'SourceAction')
    for source_action in dash.constants.SourceAction.get_all():
        try:
            SourceAction.objects.get(action=source_action)
        except SourceAction.DoesNotExist:
            SourceAction.objects.create(action=source_action)


def source_action_initial_data_reverse_code(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0023_auto_20150316_0942'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(1, b'Can update state'), (2, b'Can update CPC'), (5, b'Has 3rd party dashboard'), (4, b'Can manage content ads'), (3, b'Can update daily budget')]),
        ),
        migrations.RunPython(
            code=source_action_initial_data_forwards_code,
            reverse_code=source_action_initial_data_reverse_code,
            atomic=True,
        ),
    ]
