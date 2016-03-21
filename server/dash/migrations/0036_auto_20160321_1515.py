# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0035_auto_20160318_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignsettings',
            name='automatic_landing_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='daily_budget_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default daily budget'),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='default_cpc_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default CPC'),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='mobile_cpc_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default CPC (if ad group is targeting mobile only)'),
        ),
        migrations.AlterField(
            model_name='useractionlog',
            name='action_type',
            field=models.PositiveSmallIntegerField(choices=[(30, b'Delete Campaign Goal'), (14, b'Set Campaign Budget'), (7, b'Archive/Restore Ad Group'), (27, b'Set Account Publisher Blacklist'), (3, b'Archive/Restore Content Ad(s)'), (16, b'Create Conversion Goal'), (22, b'Schedule report'), (2, b'Set Content Ad(s) State'), (23, b'Delete scheduled report'), (5, b'Set Ad Group Settings'), (11, b'Create Campaign'), (13, b'Set Campaign Agency Settings'), (8, b'Create Account'), (1, b'Upload Content Ads'), (19, b'Archive/Restore Conversion Pixel'), (28, b'Set Global Publisher Blacklist'), (10, b'Archive/Restore Account'), (24, b'Direct report download'), (26, b'Set Campaign Publisher Blacklist'), (15, b'Archive/Restore Campaign'), (18, b'Create Conversion Pixel'), (21, b'Set Media Source Settings'), (20, b'Create Media Source Campaign'), (32, b'Change Primary Campaign Goal'), (31, b'Change Campaign Goal Value'), (17, b'Delete Conversion Goal'), (9, b'Set Account Agency Settings'), (29, b'Create Campaign Goal'), (12, b'Set Campaign Settings'), (25, b'Set Ad Group Publisher Blacklist'), (6, b'Set Ad Group Settings (with auto added Media Sources)'), (4, b'Create Ad Group')]),
        ),
    ]
