# Generated by Django 2.1.2 on 2019-04-29 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0403_auto_20190429_1421")]

    operations = [
        migrations.AlterField(model_name="account", name="archived", field=models.BooleanField(default=False)),
        migrations.AlterField(model_name="adgroup", name="archived", field=models.BooleanField(default=False)),
        migrations.AlterField(model_name="campaign", name="archived", field=models.BooleanField(default=False)),
    ]