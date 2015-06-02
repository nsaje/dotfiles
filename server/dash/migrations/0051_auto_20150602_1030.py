# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0050_uploadbatch_inc_desc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(7, b'Can modify end date'), (4, b'Can manage content ads'), (3, b'Can update daily budget automatically'), (9, b'Can modify tracking codes'), (1, b'Can update state'), (2, b'Can update CPC'), (14, b'Can modify ad group IAB category manually'), (11, b'Can modify ad group IAB category automatically'), (13, b'Can update daily budget manually'), (10, b'Can modify adgroup name'), (5, b'Has 3rd party dashboard'), (6, b'Can modify start date'), (8, b'Can modify device and geo targeting'), (12, b'Update tracking codes on content ads')]),
        ),
    ]
