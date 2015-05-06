# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_settings_to_batch(apps, schema_editor):
    ContentAd = apps.get_model('dash', 'ContentAd')
    AdGroup = apps.get_model('dash', 'AdGroup')
    AdGroupSettings = apps.get_model('dash', 'AdGroupSettings')

    for ad_group in AdGroup.objects.all():
        settings = AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            display_url = settings[0].display_url
            brand_name = settings[0].brand_name
            description = settings[0].description
            call_to_action = settings[0].call_to_action
        else:
            display_url = None
            brand_name = None
            description = None
            call_to_action = None

        batches = {}
        for content_ad in ContentAd.objects.filter(ad_group=ad_group).select_related('batch'):
            batch = content_ad.batch

            if batch.id not in batches:
                batches[batch.id] = batch

        for batch in batches.values():
            batch.display_url = display_url
            batch.brand_name = brand_name
            batch.description = description
            batch.call_to_action = call_to_action
            batch.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0037_auto_20150504_1724'),
    ]

    operations = [
        migrations.RunPython(copy_settings_to_batch)
    ]
