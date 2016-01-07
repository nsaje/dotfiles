# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_auto_20151230_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='publisherblacklist',
            name='external_id',
            field=models.CharField(max_length=127, null=True, verbose_name=b'External ID'),
        ),
    ]
