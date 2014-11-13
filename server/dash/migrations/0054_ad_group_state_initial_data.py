# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards_copy_settings(apps, schema_editor):
    AdGroupSourceSettings = apps.get_model('dash', 'AdGroupSourceSettings')
    AdGroupSourceState = apps.get_model('dash', 'AdGroupSourceState')

    if len(AdGroupSourceState.objects.all()) > 0:
        return

    latest_settings = AdGroupSourceSettings.objects.\
        distinct('ad_group_source_id').\
        order_by('ad_group_source_id', '-created_dt')

    for settings in latest_settings:
        AdGroupSourceState.objects.create(
            ad_group_source=settings.ad_group_source,
            created_dt=settings.created_dt,
            state=settings.state,
            cpc_cc=settings.cpc_cc,
            daily_budget_cc=settings.daily_budget_cc
        )


def reverse_copy_settings(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0053_auto_20141111_1551'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards_copy_settings,
            reverse_code=reverse_copy_settings
        )
    ]
