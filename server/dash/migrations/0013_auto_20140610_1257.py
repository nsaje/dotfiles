# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0012_auto_20140606_1030'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='account',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='network',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='state',
            field=models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')]),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='account',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='daily_budget_cc',
            field=models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at'),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='cpc_cc',
            field=models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
    ]
