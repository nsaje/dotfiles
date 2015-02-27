# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0019_auto_20150226_1359'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='brand_name',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='call_to_action',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='description',
            field=models.CharField(default=b'', max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='short_name',
            field=models.CharField(default=b'', max_length=25, blank=True),
            preserve_default=True,
        ),
    ]
