# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-11 15:18
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0353_cpm_buying_local_b1_cpm")]

    operations = [
        migrations.AlterField(
            model_name="adgroupsettings",
            name="b1_sources_group_cpm",
            field=models.DecimalField(
                decimal_places=4, default=Decimal("0.01"), max_digits=10, verbose_name="Bidder's Bid CPM"
            ),
        )
    ]