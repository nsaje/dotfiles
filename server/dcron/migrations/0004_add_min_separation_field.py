# Generated by Django 2.1.2 on 2018-11-13 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dcron", "0003_add_max_duration_field")]

    operations = [
        migrations.AddField(
            model_name="dcronjobsettings",
            name="min_separation",
            field=models.FloatField(default=30),
            preserve_default=False,
        )
    ]
