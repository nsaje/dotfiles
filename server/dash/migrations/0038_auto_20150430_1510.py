# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from dash import constants


def set_can_manage_content_ads(apps, schema_editor):
    AdGroupSource = apps.get_model('dash', 'AdGroupSource')
    for ad_group_source in AdGroupSource.objects.all():
        can_manage = ad_group_source.source.source_type.available_actions.filter(
            action=constants.SourceAction.CAN_MANAGE_CONTENT_ADS).exists()

        ad_group_source.can_manage_content_ads = (
            can_manage and
            not ad_group_source.source.maintenance and
            not ad_group_source.source.deprecated
        )

        ad_group_source.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0037_adgroupsource_can_manage_content_ads'),
    ]

    operations = [
        migrations.RunPython(set_can_manage_content_ads)
    ]
