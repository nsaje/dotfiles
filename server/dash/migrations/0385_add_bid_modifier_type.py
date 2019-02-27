# Generated by Django 2.1.2 on 2019-02-14 08:50

from django.db import migrations, models

from core.features.bid_modifiers import constants


def fill_publisher_type(apps, schema_editor):
    BidModifier = apps.get_model("dash", "BidModifier")
    BidModifier.objects.update(type=constants.BidModifierType.PUBLISHER)


class Migration(migrations.Migration):

    dependencies = [("dash", "0384_auto_20190213_1308")]

    operations = [
        migrations.AddField(
            model_name="bidmodifier",
            name="type",
            field=models.IntegerField(
                choices=[
                    (1, "Publisher"),
                    (2, "Source"),
                    (3, "Device"),
                    (4, "Operating System"),
                    (5, "Placement"),
                    (6, "Country"),
                    (7, "State"),
                    (8, "DMA"),
                ],
                null=True,
            ),
        ),
        migrations.RunPython(fill_publisher_type, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bidmodifier",
            name="type",
            field=models.IntegerField(
                choices=[
                    (1, "Publisher"),
                    (2, "Source"),
                    (3, "Device"),
                    (4, "Operating System"),
                    (5, "Placement"),
                    (6, "Country"),
                    (7, "State"),
                    (8, "DMA"),
                ]
            ),
        ),
    ]