# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0026_auto_20150408_0853'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='ad_group_name',
            field=models.CharField(default=b'', max_length=127, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(10, b'Can modify adgroup name'), (7, b'Can modify end date'), (5, b'Has 3rd party dashboard'), (4, b'Can manage content ads'), (3, b'Can update daily budget'), (6, b'Can modify start date'), (9, b'Can modify tracking codes'), (1, b'Can update state'), (2, b'Can update CPC'), (8, b'Can modify device and geo targeting')]),
        ),
    ]
