# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0043_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsource',
            name='source_content_ad_id',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='contentadsource',
            name='submission_status',
            field=models.IntegerField(default=-1, choices=[(1, b'Pending'), (4, b'Limit reached'), (-1, b'Not submitted'), (2, b'Approved'), (3, b'Rejected')]),
        ),
    ]
