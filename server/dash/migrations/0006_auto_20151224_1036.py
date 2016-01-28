# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_budgetlineitem_freed_cc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractionlog',
            name='action_type',
            field=models.PositiveSmallIntegerField(choices=[(1, b'Upload Content Ads'), (14, b'Set Campaign Budget'), (7, b'Archive/Restore Ad Group'), (25, b'Direct report download'), (10, b'Archive/Restore Account'), (3, b'Archive/Restore Content Ad(s)'), (16, b'Create Conversion Goal'), (22, b'Schedule report'), (2, b'Set Content Ad(s) State'), (19, b'Archive/Restore Conversion Pixel'), (24, b'Delete scheduled report'), (15, b'Archive/Restore Campaign'), (18, b'Create Conversion Pixel'), (21, b'Set Media Source Settings'), (20, b'Create Media Source Campaign'), (5, b'Set Ad Group Settings'), (11, b'Create Campaign'), (17, b'Delete Conversion Goal'), (9, b'Set Account Agency Settings'), (12, b'Set Campaign Settings'), (13, b'Set Campaign Agency Settings'), (23, b'Download scheduled report'), (6, b'Set Ad Group Settings (with auto added Media Sources)'), (8, b'Create Account'), (4, b'Create Ad Group')]),
        ),
    ]
