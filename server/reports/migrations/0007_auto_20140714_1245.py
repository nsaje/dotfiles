# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_remove_articlestats_cpc_cc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlestats',
            name='ad_group',
            field=models.ForeignKey(to='dash.AdGroup', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='article',
            field=models.ForeignKey(to='dash.Article', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='network',
            field=models.ForeignKey(to='dash.Network', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
