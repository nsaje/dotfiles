# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_uploadbatch_num_errors'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsource',
            name='can_manage_content_ads',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
