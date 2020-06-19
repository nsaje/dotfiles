# Generated by Django 2.1.11 on 2020-06-09 08:18

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0464_historystacktrace_created_dt"), ("automation", "0062_auto_20200609_0807")]

    operations = [
        migrations.AddField(
            model_name="rule",
            name="accounts_included",
            field=models.ManyToManyField(related_name="accounts_included", to="dash.Account"),
        ),
        migrations.AddField(
            model_name="rule",
            name="campaigns_included",
            field=models.ManyToManyField(related_name="campaigns_included", to="dash.Campaign"),
        ),
        migrations.AlterField(
            model_name="rule",
            name="ad_groups_included",
            field=models.ManyToManyField(related_name="ad_groups_included", to="dash.AdGroup"),
        ),
    ]
