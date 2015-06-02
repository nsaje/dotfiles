# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0049_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='description',
            field=models.CharField(default=b'', max_length=140, blank=True),
        ),
        migrations.AlterField(
            model_name='uploadbatch',
            name='description',
            field=models.CharField(default=b'', max_length=140, blank=True),
        ),
    ]
