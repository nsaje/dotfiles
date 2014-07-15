# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='title',
            field=models.CharField(max_length=256, editable=False),
        ),
        migrations.AlterField(
            model_name='article',
            name='url',
            field=models.CharField(max_length=2048, editable=False),
        ),
    ]
