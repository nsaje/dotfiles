# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_auto_20140716_1508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articlestats',
            name='network',
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Created at'),
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterUniqueTogether(
            name='articlestats',
            unique_together=set([(b'datetime', b'ad_group', b'article', b'source')]),
        ),
    ]
