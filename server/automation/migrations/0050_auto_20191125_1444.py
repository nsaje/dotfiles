# Generated by Django 2.1.11 on 2019-11-25 14:44

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("automation", "0049_auto_20191113_1757")]

    operations = [
        migrations.AlterField(
            model_name="rulecondition",
            name="left_operand_modifier",
            field=models.FloatField(blank=True, default=1.0, null=True),
        )
    ]