# Generated by Django 2.1.11 on 2020-01-21 15:52

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0446_agency_available_sources")]

    operations = [
        migrations.AddField(
            model_name="directdeal",
            name="account",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="dash.Account"
            ),
        )
    ]