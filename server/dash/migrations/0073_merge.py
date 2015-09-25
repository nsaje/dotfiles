# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0072_auto_20150911_1004'),
        ('dash', '0072_auto_20150910_1547')
    ]

    operations = [
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='auto_add',
            field=models.BooleanField(default=False, verbose_name=b'Automatically add this source to ad group at creation'),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default daily budget', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='default_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='mobile_cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'Default CPC (if ad group is targeting mobile only)', max_digits=10, decimal_places=4, blank=True),
        ),
    ]

