# Generated by Django 2.1.11 on 2019-12-04 09:20

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("automation", "0050_auto_20191125_1444")]

    operations = [
        migrations.AlterField(model_name="rule", name="change_limit", field=models.FloatField(blank=True, null=True)),
        migrations.AlterField(model_name="rule", name="change_step", field=models.FloatField(blank=True, null=True)),
        migrations.AlterField(
            model_name="rulecondition",
            name="right_operand_type",
            field=models.IntegerField(
                choices=[
                    (1, "Absolute value"),
                    (2, "Constant"),
                    (3, "Current date"),
                    (4, "Account manager"),
                    (5, "Campaign goal"),
                    (6, "Campaign budget"),
                    (7, "Remaining campaign budget"),
                    (8, "Ad group bid"),
                    (9, "Ad group click daily cap"),
                    (10, "Daily cap"),
                    (11, "Total spend"),
                    (12, "Total spend (daily average)"),
                ]
            ),
        ),
    ]
