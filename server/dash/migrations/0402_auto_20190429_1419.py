# Generated by Django 2.1.2 on 2019-04-29 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0401_auto_20190424_1258")]

    operations = [
        migrations.AddField(model_name="account", name="archived", field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name="adgroup", name="archived", field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name="campaign", name="archived", field=models.BooleanField(blank=True, null=True)),
    ]