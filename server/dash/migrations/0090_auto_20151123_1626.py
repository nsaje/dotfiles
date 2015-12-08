# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0089_account_uses_credits'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignsettings',
            name='target_devices',
            field=jsonfield.fields.JSONField(default=[], blank=True),
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='target_regions',
            field=jsonfield.fields.JSONField(default=[], blank=True),
        ),
    ]
