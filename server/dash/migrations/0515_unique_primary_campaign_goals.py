# Generated by Django 2.2.17 on 2021-01-20 11:53

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0514_agency_uses_source_groups")]

    operations = [
        migrations.AddConstraint(
            model_name="campaigngoal",
            constraint=models.UniqueConstraint(
                condition=models.Q(primary=True), fields=("campaign",), name="unique_primary_goal"
            ),
        )
    ]