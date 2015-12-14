# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0097_auto_20151211_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publisherblacklist',
            name='name',
            field=models.CharField(max_length=127, verbose_name=b'Publisher name'),
        ),
    ]
