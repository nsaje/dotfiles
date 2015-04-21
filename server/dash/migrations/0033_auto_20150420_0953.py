# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0032_auto_20150417_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='can_delete_traffic_metrics',
            field=models.BooleanField(default=False, verbose_name=b'Delete traffic metrics on empty report'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sourcetype',
            name='delete_traffic_metrics_threshold',
            field=models.IntegerField(default=0, verbose_name=b'Max clicks allowed to delete per daily report'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(10, b'Can modify adgroup name'), (7, b'Can modify end date'), (5, b'Has 3rd party dashboard'), (11, b'Can modify ad group IAB category'), (4, b'Can manage content ads'), (3, b'Can update daily budget'), (6, b'Can modify start date'), (9, b'Can modify tracking codes'), (1, b'Can update state'), (2, b'Can update CPC'), (8, b'Can modify device and geo targeting')]),
        ),
    ]
