# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0017_auto_20160127_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupsettings',
            name='cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Maximum CPC', max_digits=10, decimal_places=4, blank=True),
        ),
    ]
