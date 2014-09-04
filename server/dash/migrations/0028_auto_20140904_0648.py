# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0027_auto_20140903_1537'),
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
    ]
