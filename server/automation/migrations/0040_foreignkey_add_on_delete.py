# Generated by Django 2.1.2 on 2018-10-15 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("automation", "0039_auto_20180823_1551")]

    operations = [
        migrations.AlterField(
            model_name="campaignstopstate",
            name="campaign",
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to="dash.Campaign"),
        ),
        migrations.AlterField(
            model_name="realtimecampaigndatahistory",
            name="campaign",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="dash.Campaign"),
        ),
        migrations.AlterField(
            model_name="realtimecampaignstoplog",
            name="campaign",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="dash.Campaign"),
        ),
        migrations.AlterField(
            model_name="realtimedatahistory",
            name="ad_group",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="dash.AdGroup"),
        ),
        migrations.AlterField(
            model_name="realtimedatahistory",
            name="source",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="dash.Source"),
        ),
    ]
