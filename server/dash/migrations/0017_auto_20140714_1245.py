# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0016_auto_20140710_0934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupnetwork',
            name='ad_group',
            field=models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroupnetwork',
            name='network',
            field=models.ForeignKey(to='dash.Network', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='ad_group_network',
            field=models.ForeignKey(to='dash.AdGroupNetwork', on_delete=django.db.models.deletion.PROTECT, null=True),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='ad_group',
            field=models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='article',
            name='ad_group',
            field=models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
