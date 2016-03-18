# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0034_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaignsettings',
            name='automatic_landing_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='daily_budget_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default daily budget'),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='default_cpc_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default CPC'),
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='mobile_cpc_cc',
            field=models.DecimalField(decimal_places=4, max_digits=10, blank=True, help_text=b'This setting has moved. See Source model.', null=True, verbose_name=b'Default CPC (if ad group is targeting mobile only)'),
        ),
    ]
