# Generated by Django 2.1.2 on 2018-11-07 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0360_merge_20181105_1201")]

    operations = [
        migrations.AddField(
            model_name="accountsettings",
            name="frequency_capping",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="adgroupsettings",
            name="frequency_capping",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="campaignsettings",
            name="frequency_capping",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]