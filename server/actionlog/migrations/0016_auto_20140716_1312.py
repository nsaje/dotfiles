# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0015_auto_20140714_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlog',
            name='ad_group_source',
            field=models.ForeignKey(to='dash.AdGroupSource', on_delete=django.db.models.deletion.PROTECT, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='modified_dt',
            field=models.DateTimeField(null=True, verbose_name=b'Modified at', blank=True),
        ),
        migrations.AlterField(
            model_name='actionlogorder',
            name='order_type',
            field=models.IntegerField(choices=[(3, b'AdGroup Settings Update'), (2, b'Stop all'), (1, b'Fetch all'), (5, b'Fetch status'), (4, b'Fetch reports')]),
        ),
    ]
