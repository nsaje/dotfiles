# Generated by Django 2.1.11 on 2019-12-17 22:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dash", "0444_auto_20191212_1111")]

    operations = [migrations.RenameField(model_name="uploadbatch", old_name="default_state", new_name="state_override")]
