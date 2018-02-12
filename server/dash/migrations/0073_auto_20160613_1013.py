# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-13 10:13


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0072_auto_20160610_0844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplate',
            name='template_type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(2, b'Campaign settings change'), (3, b'Budget change'), (12, b'Autopilot initialisation notification'), (5, b'User password reset'), (6, b'New user introduction email'), (4, b'New conversion pixel'), (8, b'Scheduled report'), (7, b'Supply report'), (1, b'Ad group settings change'), (14, b'Campaign is running out of budget notification'), (9, b'Depleting budget notification'), (15, b'Demo is running'), (10, b'Campaign stopped notification'), (13, b'Campaign switched to landing mode notification'), (11, b'Autopilot changes notification')], null=True),
        ),
    ]
