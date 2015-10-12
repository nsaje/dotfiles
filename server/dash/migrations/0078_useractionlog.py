# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0077_accountsettings_service_fee'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActionLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('action_type', models.PositiveSmallIntegerField(choices=[(1, b'Upload Content Ads'), (14, b'Set Campaign Budget'), (7, b'Archive/Restore Ad Group'), (10, b'Archive/Restore Account'), (3, b'Archive/Restore Content Ad(s)'), (16, b'Create Conversion Goal'), (2, b'Set Content Ad(s) State'), (19, b'Archive/Restore Conversion Pixel'), (21, b'Set Media Source Settings'), (15, b'Archive/Restore Campaign'), (18, b'Create Conversion Pixel'), (20, b'Create Media Source Campaign'), (5, b'Set Ad Group Settings'), (11, b'Create Campaign'), (17, b'Delete Conversion Goal'), (9, b'Set Account Agency Settings'), (12, b'Set Campaign Settings'), (13, b'Set Campaign Agency Settings'), (6, b'Set Ad Group Settings (with auto added Media Sources)'), (8, b'Create Account'), (4, b'Create Ad Group')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Account', null=True)),
                ('account_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AccountSettings', null=True)),
                ('ad_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroup', null=True)),
                ('ad_group_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.AdGroupSettings', null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.Campaign', null=True)),
                ('campaign_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.CampaignSettings', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
