# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0072_auto_20150910_1416'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='defaultsourcesettings',
            name='desktop_cpc_cc',
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='default_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='mobile_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC (if mobile targeting)', max_digits=10, decimal_places=4, blank=True),
        ),
    ]
