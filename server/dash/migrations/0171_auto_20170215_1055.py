# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-15 10:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0170_add_wcr_email'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='publishergroup',
            options={'ordering': ('pk',)},
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='default_cs_representative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='agency',
            name='cs_representative',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='template_type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(3, b'Budget change'), (12, b'Autopilot initialisation notification'), (5, b'User password reset'), (19, b'Google Analytics Setup Instructions'), (21, b'Depleting credits'), (6, b'New user introduction email'), (18, b'Unused Outbrain accounts running out'), (23, b'Weekly client report'), (8, b'Scheduled report'), (7, b'Supply report'), (16, b'Livestream sesion id'), (17, b'Daily management report'), (1, b'Ad group settings change'), (14, b'Campaign is running out of budget notification'), (9, b'Depleting budget notification'), (15, b'Demo is running'), (10, b'Campaign stopped notification'), (11, b'Autopilot changes notification'), (2, b'Campaign settings change'), (20, b'Report results'), (13, b'Campaign switched to landing mode notification'), (4, b'New conversion pixel')], null=True),
        ),
    ]
