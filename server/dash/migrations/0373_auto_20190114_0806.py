# Generated by Django 2.1.2 on 2019-01-14 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0372_merge_20181218_1237")]

    operations = [
        migrations.AddField(
            model_name="submissionfilter", name="description", field=models.TextField(blank=True, null=True)
        ),
        migrations.AddField(
            model_name="submissionfilter",
            name="modified_dt",
            field=models.DateTimeField(auto_now=True, verbose_name="Modified at"),
        ),
    ]