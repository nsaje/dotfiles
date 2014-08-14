# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_auto_20140724_1638'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'permissions': ((b'account_automatically_assigned', b'All new accounts are automatically added to user.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={'permissions': ((b'campaign_automatically_assigned', b'All new campaigns are automatically added to user.'),)},
        ),
    ]
