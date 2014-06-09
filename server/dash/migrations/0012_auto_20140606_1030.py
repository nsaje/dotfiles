# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0011_auto_20140605_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='cpc_cc',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='cpc_cc',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True),
        ),
    ]
