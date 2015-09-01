# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0017_auto_20150817_1343'),
    ]

    operations = [
        migrations.RunSQL("""
        CREATE TABLE contentadstats (
            id integer PRIMARY KEY,
            datetime timestamp,
            content_ad_id integer,
            adgroup_id integer,
            source_id integer,
            campaign_id integer,
            account_id integer,

            impressions integer,
            clicks integer,
            cost_cc integer,
            data_cost_cc integer,

            visits integer,
            new_visits integer,
            bounced_visits integer,
            pageviews integer,
            total_time_on_site integer,

            conversions varchar(256),
            touchpoints varchar(256)
        );
        """)
    ]
