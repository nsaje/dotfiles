# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0071_remove_batch_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default daily budget', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='desktop_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC (desktop/default)', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='mobile_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC (if mobile)', max_digits=10, decimal_places=4, blank=True),
        ),
    ]
