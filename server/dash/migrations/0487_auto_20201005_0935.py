# Generated by Django 2.1.11 on 2020-10-05 09:35

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0486_auto_20200929_1144")]

    operations = [
        migrations.AddField(
            model_name="agency", name="uses_realtime_autopilot", field=models.BooleanField(default=False)
        )
    ]