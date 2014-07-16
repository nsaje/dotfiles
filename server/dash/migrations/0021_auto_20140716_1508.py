# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import dash.models


def migrate_data(apps, schema_editor):
    networks = dash.models.Network.objects.all().order_by('id')
    for network in networks:
        dash.models.Source.objects.create(
            id=network.id,
            type=network.type,
            name=network.name,
            maintenance=network.maintenance,
            created_dt=network.created_dt,
            modified_dt=network.modified_dt,
        )

    network_credentialss = dash.models.NetworkCredentials.objects.all().order_by('created_dt')
    for network_credentials in network_credentialss:
        dash.models.SourceCredentials.objects.create(
            id=network_credentials.id,
            source=dash.models.Source.objects.get(id=network_credentials.network.id),
            name=network_credentials.name,
            credentials=network_credentials.credentials,
            created_dt=network_credentials.created_dt,
            modified_dt=network_credentials.modified_dt,
        )

    ad_group_networks = dash.models.AdGroupNetwork.objects.all().order_by('id')
    for ad_group_network in ad_group_networks:
        dash.models.AdGroupSource.objects.create(
            id=ad_group_network.id,
            ad_group=ad_group_network.ad_group,
            source=dash.models.Source.objects.get(id=ad_group_network.network.id),
            source_credentials=dash.models.SourceCredentials.objects.get(id=ad_group_network.network_credentials.id),
            source_campaign_key=ad_group_network.network_campaign_key,
        )

    ad_group_network_settingss = dash.models.AdGroupNetworkSettings.objects.all().order_by('id')
    for ad_group_network_settings in ad_group_network_settingss:
        dash.models.AdGroupSourceSettings.objects.create(
            id=ad_group_network_settings.id,
            ad_group_source=dash.models.AdGroupSource.objects.get(id=ad_group_network_settings.ad_group_network.id),
            created_dt=ad_group_network_settings.created_dt,
            created_by=ad_group_network_settings.created_by,
            state=ad_group_network_settings.state,
            cpc_cc=ad_group_network_settings.cpc_cc,
            daily_budget_cc=ad_group_network_settings.daily_budget_cc,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0020_auto_20140716_1507'),
    ]

    operations = [
        migrations.RunPython(migrate_data)
    ]
