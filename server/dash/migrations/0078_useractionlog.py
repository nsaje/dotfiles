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
                ('action_type', models.PositiveSmallIntegerField(choices=[(0, b'Upload Content Ads'), (13, b'Set Campaign Budget'), (6, b'Archive/Restore Ad Group'), (9, b'Archive/Restore Account'), (2, b'Archive/Restore Content Ad(s)'), (15, b'Create Conversion Goal'), (1, b'Set Content Ad(s) State'), (18, b'Archive/Restore Conversion Pixel'), (20, b'Set Media Source Settings'), (14, b'Archive/Restore Campaign'), (17, b'Create Conversion Pixel'), (19, b'Create Media Source Campaign'), (4, b'Set Ad Group Settings'), (10, b'Create Campaign'), (16, b'Delete Conversion Goal'), (8, b'Set Account Agency Settings'), (11, b'Set Campaign Settings'), (12, b'Set Campaign Agency Settings'), (5, b'Set Ad Group Settings (with auto added Media Sources)'), (7, b'Create Account'), (3, b'Create Ad Group')])),
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
