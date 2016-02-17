# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_uploadbatch_propagated_content_ads'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='cancelled',
            field=models.BooleanField(default=False),
        ),
    ]
