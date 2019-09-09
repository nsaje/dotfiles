# Generated by Django 2.1.11 on 2019-09-04 09:41

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0424_create_source_bid_modifiers")]

    operations = [
        migrations.AddField(
            model_name="contentad", name="icon_file_size", field=models.PositiveIntegerField(null=True)
        ),
        migrations.AddField(
            model_name="contentad", name="icon_hash", field=models.CharField(max_length=128, null=True)
        ),
        migrations.AddField(
            model_name="contentad", name="icon_id", field=models.CharField(editable=False, max_length=256, null=True)
        ),
        migrations.AddField(model_name="contentad", name="icon_size", field=models.PositiveIntegerField(null=True)),
        migrations.AddField(
            model_name="contentadcandidate", name="icon_file_size", field=models.PositiveIntegerField(null=True)
        ),
        migrations.AddField(
            model_name="contentadcandidate", name="icon_hash", field=models.CharField(max_length=128, null=True)
        ),
        migrations.AddField(
            model_name="contentadcandidate", name="icon_height", field=models.PositiveIntegerField(null=True)
        ),
        migrations.AddField(
            model_name="contentadcandidate", name="icon_id", field=models.CharField(max_length=256, null=True)
        ),
        migrations.AddField(
            model_name="contentadcandidate",
            name="icon_status",
            field=models.IntegerField(
                choices=[(1, "Pending"), (2, "Waiting for response"), (3, "OK"), (4, "Failed")], default=1
            ),
        ),
        migrations.AddField(
            model_name="contentadcandidate",
            name="icon_url",
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="contentadcandidate", name="icon_width", field=models.PositiveIntegerField(null=True)
        ),
    ]