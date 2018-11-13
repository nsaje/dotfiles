# Generated by Django 2.1.2 on 2018-11-07 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dcron", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="dcronjob",
            name="alert",
            field=models.IntegerField(
                choices=[(0, "OK"), (1, "Execution"), (2, "Duration"), (3, "Failure")], default=0
            ),
        )
    ]
