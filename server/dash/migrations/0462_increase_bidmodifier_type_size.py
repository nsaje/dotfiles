# Generated by Django 2.1.11 on 2020-05-06 11:51

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0461_auto_20200507_1135")]

    operations = [
        migrations.AlterField(
            model_name="bidmodifier",
            name="target",
            field=models.CharField(max_length=400, verbose_name="Bid modifier target"),
        )
    ]