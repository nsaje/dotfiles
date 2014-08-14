# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0008_auto_20140813_0858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': (b'-created_dt',), 'permissions': ((b'group_account_automatically_add', b'All new accounts are automatically added to group.'),)},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
    ]
