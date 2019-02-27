# Generated by Django 2.1.2 on 2019-02-15 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dash", "0388_change_bid_modifier_unique_together")]

    operations = [
        migrations.AlterField(
            model_name="bidmodifier",
            name="source",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="dash.Source"
            ),
        )
    ]