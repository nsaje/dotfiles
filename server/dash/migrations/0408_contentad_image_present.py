# Generated by Django 2.1.2 on 2019-05-06 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0407_ad_group_archived_backfill")]

    operations = [
        migrations.AddField(model_name="contentad", name="image_present", field=models.BooleanField(default=True))
    ]