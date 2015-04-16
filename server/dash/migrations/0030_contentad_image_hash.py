# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0029_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='image_hash',
            field=models.CharField(max_length=128, null=True),
            preserve_default=True,
        ),
    ]
