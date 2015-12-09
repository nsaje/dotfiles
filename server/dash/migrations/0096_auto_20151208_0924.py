# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0095_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetlineitem',
            name='freed_cc',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='publisherblacklist',
            name='everywhere',
            field=models.BooleanField(default=False, verbose_name=b'globally blacklisted'),
        ),
        migrations.AlterField(
            model_name='publisherblacklist',
            name='status',
            field=models.IntegerField(default=2, choices=[(2, b'Blacklisted'), (1, b'Enabled'), (3, b'Pending')]),
        ),
    ]
