# Generated by Django 2.1.2 on 2019-03-19 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0397_auto_20190319_0838")]

    operations = [
        migrations.AlterField(
            model_name="whitelabel",
            name="theme",
            field=models.CharField(
                blank=True,
                choices=[
                    ("greenpark", "Green Park Content"),
                    ("adtechnacity", "Adtechnacity"),
                    ("newscorp", "Newscorp"),
                    ("burda", "Burda"),
                    ("mediamond", "Mediamond"),
                    ("amplify", "Amplify"),
                ],
                max_length=255,
            ),
        )
    ]
