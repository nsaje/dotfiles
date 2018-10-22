# Generated by Django 2.1.2 on 2018-10-19 09:42

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0355_cpm_buying_sourcetype")]

    operations = [
        migrations.AlterField(
            model_name="source",
            name="default_cpm",
            field=models.DecimalField(
                decimal_places=4, default=Decimal("1.00"), max_digits=10, verbose_name="Default CPM"
            ),
        ),
        migrations.AlterField(
            model_name="source",
            name="default_mobile_cpm",
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal("1.00"),
                max_digits=10,
                verbose_name="Default CPM (if ad group is targeting mobile only)",
            ),
        ),
    ]
