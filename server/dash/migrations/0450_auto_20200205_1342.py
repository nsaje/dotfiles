# Generated by Django 2.1.11 on 2020-02-05 13:42

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0449_merge_20200203_0919")]

    operations = [
        migrations.AddField(
            model_name="reportjob",
            name="end_dt",
            field=models.DateTimeField(null=True, verbose_name="Finished processing at"),
        ),
        migrations.AddField(
            model_name="reportjob",
            name="modified_dt",
            field=models.DateTimeField(auto_now=True, null=True, verbose_name="Modified at"),
        ),
        migrations.AddField(
            model_name="reportjob",
            name="start_dt",
            field=models.DateTimeField(null=True, verbose_name="Started processing at"),
        ),
    ]
