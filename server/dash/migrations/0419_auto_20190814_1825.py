# Generated by Django 2.1.8 on 2019-08-14 18:25

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0418_uploadbatch_default_state")]

    operations = [
        migrations.AlterField(
            model_name="uploadbatch",
            name="default_state",
            field=models.IntegerField(choices=[(1, "Enabled"), (2, "Paused")], default=1, null=True),
        ),
        migrations.AlterField(
            model_name="uploadbatch",
            name="type",
            field=models.IntegerField(choices=[(1, "Insert"), (2, "Edit"), (3, "Clone")], default=1),
        ),
    ]