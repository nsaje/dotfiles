# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-29 13:50


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0194_auto_20170327_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='whitelabel',
            field=models.CharField(blank=True, choices=[(b'greenpark', b'Green Park Content'), (b'adtechnacity', b'Adtechnacity')], max_length=255),
        ),
    ]
