# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-07 13:28


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0133_auto_20161004_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='b1_sources_group_daily_budget',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=10, null=True, verbose_name=b"Bidder's Daily Budget"),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='b1_sources_group_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='b1_sources_group_state',
            field=models.IntegerField(choices=[(1, b'Enabled'), (2, b'Paused')], default=2),
        ),
        migrations.AlterField(
            model_name='publisherblacklist',
            name='status',
            field=models.IntegerField(choices=[(2, b'Blacklisted'), (1, b'Active'), (3, b'Pending')], default=2),
        ),
    ]
