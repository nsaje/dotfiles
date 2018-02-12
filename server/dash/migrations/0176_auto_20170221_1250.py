# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 12:50


import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0175_auto_20170221_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='accountsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='blacklist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='whitelist_publisher_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, default=list, null=True, size=None),
        ),
    ]
