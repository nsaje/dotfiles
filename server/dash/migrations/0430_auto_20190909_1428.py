# Generated by Django 2.1.11 on 2019-09-09 12:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("dash", "0429_auto_20190909_1425")]

    operations = [
        migrations.AddField(
            model_name="directdeal",
            name="modified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Modified by",
            ),
        ),
        migrations.AddField(
            model_name="directdealconnection",
            name="modified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Modified by",
            ),
        ),
    ]
