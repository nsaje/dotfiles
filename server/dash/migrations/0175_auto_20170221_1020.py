# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 10:20
from __future__ import unicode_literals

import dash.models
import django.contrib.postgres.fields
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0174_add_inventory_report_email'),
    ]

    operations = [
        migrations.RunSQL('SET CONSTRAINTS ALL IMMEDIATE',
                          reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql="update dash_adgroupsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_adgroupsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, ']', '}')"),
        migrations.RunSQL(sql="update dash_adgroupsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_adgroupsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, ']', '}')"),
        migrations.RunSQL(sql="update dash_campaignsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_campaignsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, ']', '}')"),
        migrations.RunSQL(sql="update dash_campaignsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_campaignsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, ']', '}')"),
        migrations.RunSQL(sql="update dash_accountsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_accountsettings set whitelist_publisher_groups=regexp_replace(whitelist_publisher_groups, ']', '}')"),
        migrations.RunSQL(sql="update dash_accountsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, '\[', '{')"),
        migrations.RunSQL(sql="update dash_accountsettings set blacklist_publisher_groups=regexp_replace(blacklist_publisher_groups, ']', '}')"),
        migrations.CreateModel(
            name='AccountSettingsReadOnly',
            fields=[
            ],
            options={
                'abstract': False,
                'proxy': True,
            },
            bases=(dash.models.ReadOnlyModelMixin, 'dash.accountsettings'),
        ),
        migrations.CreateModel(
            name='CampaignSettingsReadOnly',
            fields=[
            ],
            options={
                'abstract': False,
                'proxy': True,
            },
            bases=(dash.models.ReadOnlyModelMixin, 'dash.campaignsettings'),
        ),
        migrations.AddField(
            model_name='publishergroupentry',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name=b'Created at'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publishergroupentry',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='template_type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(3, b'Budget change'), (12, b'Autopilot initialisation notification'), (5, b'User password reset'), (19, b'Google Analytics Setup Instructions'), (21, b'Depleting credits'), (6, b'New user introduction email'), (24, b'Pacing notification'), (18, b'Unused Outbrain accounts running out'), (23, b'Weekly client report'), (8, b'Scheduled report'), (25, b'Weekly inventory report'), (7, b'Supply report'), (16, b'Livestream sesion id'), (22, None), (17, b'Daily management report'), (1, b'Ad group settings change'), (14, b'Campaign is running out of budget notification'), (9, b'Depleting budget notification'), (15, b'Demo is running'), (10, b'Campaign stopped notification'), (11, b'Autopilot changes notification'), (2, b'Campaign settings change'), (20, b'Report results'), (13, b'Campaign switched to landing mode notification'), (4, b'New conversion pixel')], null=True),
        ),
    ]
