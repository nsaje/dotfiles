# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0006_auto_20140820_0825'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users', 'permissions': ((b'help_view', b'Can view help popovers.'), (b'supply_dash_link_view', b'Can view supply dash link.'), (b'ad_group_tracking_code_edit', b"Can edit ad group's tracking code"))},
        ),
    ]
