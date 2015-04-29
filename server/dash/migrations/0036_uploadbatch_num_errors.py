# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0035_uploadbatch_error_report_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='num_errors',
            field=models.PositiveIntegerField(null=True),
            preserve_default=True,
        ),
    ]
