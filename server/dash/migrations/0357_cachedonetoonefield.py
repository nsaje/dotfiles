# Generated by Django 2.1.2 on 2018-10-23 05:53

from django.db import migrations
import django.db.models.deletion
import utils.settings_fields


class Migration(migrations.Migration):

    dependencies = [("dash", "0356_auto_20181019_0942")]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="settings",
            field=utils.settings_fields.CachedOneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="latest_for_entity",
                to="dash.AccountSettings",
            ),
        ),
        migrations.AlterField(
            model_name="adgroup",
            name="settings",
            field=utils.settings_fields.CachedOneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="latest_for_entity",
                to="dash.AdGroupSettings",
            ),
        ),
        migrations.AlterField(
            model_name="adgroupsource",
            name="settings",
            field=utils.settings_fields.CachedOneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="latest_for_entity",
                to="dash.AdGroupSourceSettings",
            ),
        ),
        migrations.AlterField(
            model_name="agency",
            name="settings",
            field=utils.settings_fields.CachedOneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="latest_for_entity",
                to="dash.AgencySettings",
            ),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="settings",
            field=utils.settings_fields.CachedOneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="latest_for_entity",
                to="dash.CampaignSettings",
            ),
        ),
    ]