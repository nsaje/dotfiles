# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0034_auto_20150421_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsource',
            name='source_content_ad_id',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='submission_errors',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='submission_status',
            field=models.IntegerField(default=-1, choices=[(1, b'Pending'), (4, b'Limit reached'), (-1, b'Not submitted'), (2, b'Approved'), (3, b'Rejected')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='source',
            name='content_ad_submission_type',
            field=models.IntegerField(default=1, choices=[(1, b'Default'), (2, b'One submission per ad group')]),
            preserve_default=True,
        ),
    ]
