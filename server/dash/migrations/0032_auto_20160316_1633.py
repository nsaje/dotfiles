# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0031_auto_20160314_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='default_cpc_cc',
            field=models.DecimalField(default=Decimal('0.15'), verbose_name=b'Default CPC', max_digits=10, decimal_places=4),
        ),
        migrations.AddField(
            model_name='source',
            name='default_daily_budget_cc',
            field=models.DecimalField(default=Decimal('10.00'), verbose_name=b'Default daily budget', max_digits=10, decimal_places=4),
        ),
        migrations.AddField(
            model_name='source',
            name='default_mobile_cpc_cc',
            field=models.DecimalField(default=Decimal('0.15'), verbose_name=b'Default CPC (if ad group is targeting mobile only)', max_digits=10, decimal_places=4),
        ),
    ]
