# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0031_auto_20150417_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(
                serialize=False, 
                primary_key=True, 
                choices=[
                    (11, b'Can modify ad group IAB category'),
                ],
            )
        ),
        migrations.RunPython(
            code=source_action_initial_data_forwards_code,
            reverse_code=source_action_initial_data_reverse_code,
            atomic=True,
        ),

    ]
