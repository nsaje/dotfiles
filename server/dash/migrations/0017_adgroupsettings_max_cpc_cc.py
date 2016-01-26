# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0016_auto_20160126_0933'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='max_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Maximum CPC', max_digits=10, decimal_places=4, blank=True),
        ),
    ]
