# Generated by Django 2.1.11 on 2020-04-16 16:12

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("automation", "0059_auto_20200324_0107")]

    operations = [
        migrations.AlterField(
            model_name="rulecondition",
            name="left_operand_modifier",
            field=models.FloatField(blank=True, default=None, null=True),
        )
    ]