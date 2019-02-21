# Generated by Django 2.1.2 on 2019-02-20 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0390_use_bidder_slug_instead_of_tracking_slug")]

    operations = [
        migrations.AlterField(
            model_name="source",
            name="bidder_slug",
            field=models.CharField(default="", max_length=50, unique=True, verbose_name="B1 Slug"),
            preserve_default=False,
        )
    ]
