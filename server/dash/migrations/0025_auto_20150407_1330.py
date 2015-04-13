# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import dash.constants

from django.db import models, migrations

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
        ('dash', '0024_auto_20150323_1127'),
    ]

    operations = [

        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(
                serialize=False, 
                primary_key=True, 
                choices=[
                    (6, b'Can modify start date'),
                    (7, b'Can modify end date'),
                    (8, b'Can modify device and geo targeting'),
                    (9, b'Can modify tracking codes'),
                ],
            )
        ),
        migrations.RunPython(
            code=source_action_initial_data_forwards_code,
            reverse_code=source_action_initial_data_reverse_code,
            atomic=True,
        ),

    ]
