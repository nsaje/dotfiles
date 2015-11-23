# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0021_auto_20150922_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='ad_group_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True),
        ),
    ]
