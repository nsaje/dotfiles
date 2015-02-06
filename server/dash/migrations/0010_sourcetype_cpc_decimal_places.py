# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_account_outbrain_marketer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='cpc_decimal_places',
            field=models.PositiveSmallIntegerField(null=True, verbose_name=b'CPC Decimal Places', blank=True),
            preserve_default=True,
        ),
    ]
