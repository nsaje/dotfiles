# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-01-27 12:48


from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0159_auto_20170119_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='default_blacklist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='blacklisted_accounts', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='account',
            name='default_whitelist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='whitelisted_accounts', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='blacklist_publisher_groups',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='whitelist_publisher_groups',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='default_blacklist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='blacklisted_ad_groups', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='adgroup',
            name='default_whitelist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='whitelisted_ad_groups', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='default_blacklist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='blacklisted_campaigns', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='default_whitelist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='whitelisted_campaigns', to='dash.PublisherGroup'),
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='blacklist_publisher_groups',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='whitelist_publisher_groups',
            field=jsonfield.fields.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='publishergroupentry',
            name='include_subdomains',
            field=models.BooleanField(default=True),
        ),
    ]
