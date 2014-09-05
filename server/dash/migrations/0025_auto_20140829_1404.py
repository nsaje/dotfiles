# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0024_merge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AddField(
            model_name='adgroupsource',
            name='last_successful_sync_dt',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
