# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0083_publisherblacklist_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='crop_areas',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
