# Generated by Django 2.1.11 on 2019-09-19 10:48

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0430_auto_20190909_1428")]

    operations = [
        migrations.AlterField(
            model_name="history",
            name="action_type",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Change Campaign Goal"),
                    (2, "Change Budget"),
                    (3, "Change Credit"),
                    (4, "Set Publisher Blacklist"),
                    (5, "Set Global Publisher Blacklist"),
                    (6, "Manage Reporting"),
                    (7, "Set Content Ad(s) State"),
                    (8, "Change Settings"),
                    (9, "Create"),
                    (10, "Create Content Ad"),
                    (11, "Create Conversion Pixel"),
                    (12, "Archive/Restore Conversion Pixel"),
                    (13, "Archive/Restore"),
                    (14, "Archive/Restore Content Ad(s)"),
                    (15, "Set Media Source Settings"),
                    (16, "Add Media Source"),
                    (17, "Rename conversion pixel"),
                    (18, "Create custom audience"),
                    (19, "Archive custom audience"),
                    (20, "Restore custom audience"),
                    (22, "Update custom audience"),
                    (21, "Enable pixel for building audiences"),
                    (23, "Set redirect url for pixel"),
                    (24, "Remove redirect url for pixel"),
                    (25, "Create publisher group"),
                    (26, "Update publisher group"),
                    (26, "Update publisher group"),
                    (27, "Pixel set as an additional audience pixel"),
                    (28, "Create Conversion Pixel as additional audience pixel"),
                    (29, "Create deal connection"),
                    (30, "Delete deal connection"),
                ],
                null=True,
            ),
        )
    ]