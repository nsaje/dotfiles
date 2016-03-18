# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal

from django.db import migrations

defaults = {
    'b1': {
        'default_cpc_cc': Decimal('0.15'),
        'default_mobile_cpc_cc': Decimal('0.15'),
        'default_daily_budget_cc': Decimal('30.00')
    },
    'yahoo': {
        'default_cpc_cc': Decimal('0.05'),
        'default_mobile_cpc_cc': Decimal('0.05'),
        'default_daily_budget_cc': Decimal('5.00')
    },
    'outbrain': {
        'default_cpc_cc': Decimal('0.03'),
        'default_mobile_cpc_cc': Decimal('0.03'),
        'default_daily_budget_cc': Decimal('10.00')
    },
    'facebook': {
        'default_cpc_cc': Decimal('0.15'),
        'default_mobile_cpc_cc': Decimal('0.15'),
        'default_daily_budget_cc': Decimal('10.00')
    }
}


def set_source_default_settings(apps, schema_editor):

    Source = apps.get_model('dash', 'Source')
    DefaultSourceSettings = apps.get_model('dash', 'DefaultSourceSettings')

    for source in Source.objects.filter(deprecated=False):
        if source.source_type.type in defaults:
            source.default_cpc_cc = defaults[source.source_type.type]['default_cpc_cc']
            source.default_mobile_cpc_cc = defaults[source.source_type.type]['default_mobile_cpc_cc']
            source.default_daily_budget_cc = defaults[source.source_type.type]['default_daily_budget_cc']

        try:
            if source.defaultsourcesettings.default_cpc_cc:
                source.default_cpc_cc = source.defaultsourcesettings.default_cpc_cc
            if source.defaultsourcesettings.mobile_cpc_cc:
                source.default_mobile_cpc_cc = source.defaultsourcesettings.mobile_cpc_cc
            if source.defaultsourcesettings.daily_budget_cc:
                source.default_daily_budget_cc = source.defaultsourcesettings.daily_budget_cc

        except DefaultSourceSettings.DoesNotExist:
            if source.source_type.type not in defaults:
                continue

        source.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0032_auto_20160316_1633'),
    ]

    operations = [
        migrations.RunPython(set_source_default_settings)
    ]
