# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0017_auto_20140716_1509'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actionlog',
            name='ad_group_network',
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='ad_group_source',
            field=models.ForeignKey(to='dash.AdGroupSource', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Modified at', null=True),
        ),
    ]
