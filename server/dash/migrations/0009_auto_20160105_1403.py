# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0008_remove_campaignsettings_sales_representative'),
    ]

    operations = [
        migrations.RenameField(
            model_name='campaignsettings',
            old_name='account_manager',
            new_name='campaign_manager',
        ),
    ]
