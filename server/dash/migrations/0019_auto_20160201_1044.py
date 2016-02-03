# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_auto_20160127_1553'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditlineitem',
            name='flat_fee_cc',
            field=models.IntegerField(default=0, verbose_name=b'Flat fee (cc)'),
        ),
        migrations.AddField(
            model_name='creditlineitem',
            name='flat_fee_end_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='creditlineitem',
            name='flat_fee_start_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
