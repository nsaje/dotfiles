# Generated by Django 2.1.11 on 2020-04-22 17:43

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("zemauth", "0238_auto_20200421_0849")]

    operations = [
        migrations.AlterField(
            model_name="entitypermission",
            name="permission",
            field=models.CharField(
                choices=[
                    ("read", "View accounts, campaigns, ad groups and ads."),
                    ("write", "Edit accounts, campaigns, ad groups and ads."),
                    ("user", "Manage other users."),
                    ("budget", "Allocate budgets to campaigns."),
                    ("budget_margin", "Configure campaign budget margin."),
                    ("agency_spend_margin", "View agency spend and margin."),
                    ("media_cost_data_cost_licence_fee", "View media cost, data cost and licence fee."),
                    ("restapi", "RESTAPI access"),
                ],
                max_length=128,
            ),
        )
    ]
