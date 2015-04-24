# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0034_auto_20150421_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='error_report_key',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
    ]
