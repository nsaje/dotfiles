# Generated by Django 2.1.11 on 2020-05-13 14:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("etl", "0003_etlbooksclosed")]

    operations = [migrations.RenameField(model_name="etlbooksclosed", old_name="finished_time", new_name="modified_dt")]
