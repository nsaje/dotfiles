# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-17 15:20


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0267_auto_20180115_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='allowed_sources',
            field=models.ManyToManyField(to='dash.Source'),
        ),
    ]
