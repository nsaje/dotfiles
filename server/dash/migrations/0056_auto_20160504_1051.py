# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-04 10:51


from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0055_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
