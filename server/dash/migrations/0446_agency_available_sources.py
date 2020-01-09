# Generated by Django 2.1.11 on 2020-01-08 13:46

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0445_auto_20191217_2201")]

    operations = [
        migrations.AddField(
            model_name="agency",
            name="available_sources",
            field=models.ManyToManyField(blank=True, related_name="available_agencies", to="dash.Source"),
        )
    ]