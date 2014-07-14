# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0016_auto_20140710_0934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='modified_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='campaign',
            field=models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroupnetwork',
            name='network',
            field=models.ForeignKey(to='dash.Network', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroupnetwork',
            name='network_credentials',
            field=models.ForeignKey(to='dash.NetworkCredentials', on_delete=django.db.models.deletion.PROTECT, null=True),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='ad_group_network',
            field=models.ForeignKey(to='dash.AdGroupNetwork', on_delete=django.db.models.deletion.PROTECT, null=True),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='ad_group',
            field=models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='account',
            field=models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='modified_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='networkcredentials',
            name='network',
            field=models.ForeignKey(to='dash.Network', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
