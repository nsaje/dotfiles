# Generated by Django 2.1.11 on 2020-08-11 10:08

from django.db import migrations
from django.db import models

import zemauth.models.user.constants


def fill_status(apps, schema_editor):
    User = apps.get_model("zemauth", "User")
    User.objects.update(status=zemauth.models.user.constants.Status.ACTIVE)


class Migration(migrations.Migration):

    dependencies = [("zemauth", "0251_auto_20200810_0824")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.IntegerField(choices=[(1, "Invitation Pending"), (2, "Active")], default=1),
        ),
        migrations.RunPython(fill_status, reverse_code=migrations.RunPython.noop),
    ]