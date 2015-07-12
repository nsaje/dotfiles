# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import dash.constants


def forwards_code(apps, schema_editor):
    SourceAction = apps.get_model('dash', 'SourceAction')
    for source_action in dash.constants.SourceAction.get_all():
        try:
            SourceAction.objects.get(action=source_action)
        except SourceAction.DoesNotExist:
            SourceAction.objects.create(action=source_action)

    device_targeting_action = SourceAction.objects.get(action=dash.constants.SourceAction.CAN_MODIFY_DEVICE_TARGETING)
    country_targeting_action = SourceAction.objects.get(action=dash.constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING)

    SourceType = apps.get_model('dash', 'SourceType')
    for source_type in SourceType.objects.filter(available_actions=device_targeting_action):
        source_type.available_actions.add(country_targeting_action)
        source_type.save()

    # remove the non-standard mapping
    AdGroupSettings = apps.get_model('dash', 'AdGroupSettings')
    for adgroup_settings in AdGroupSettings.objects.filter(target_regions__contains='UK'):
        adgroup_settings.target_regions = ['GB' if tr == 'UK' else tr for tr in adgroup_settings.target_regions]
        adgroup_settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0057_contentad_tracker_urls'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(7, b'Can modify end date'), (4, b'Can manage content ads'), (8, b'Can modify device targeting'), (3, b'Can update daily budget automatically'), (6, b'Can modify start date'), (9, b'Can modify tracking codes'), (1, b'Can update state'), (2, b'Can update CPC'), (14, b'Can modify ad group IAB category manually'), (11, b'Can modify ad group IAB category automatically'), (13, b'Can update daily budget manually'), (10, b'Can modify adgroup name'), (5, b'Has 3rd party dashboard'), (15, b'Can modify DMA targeting'), (16, b'Can modify targeting by country'), (12, b'Update tracking codes on content ads')]),
        ),
        migrations.RunPython(code=forwards_code, reverse_code=None)
    ]
