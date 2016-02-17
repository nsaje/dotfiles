# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0017_auto_20160127_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadbatch',
            name='propagated_content_ads',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
