# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlestats',
            name='source',
            field=models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='articlestats',
            name='created_dt',
            field=models.DateTimeField(verbose_name=b'Created at'),
        ),
        migrations.AlterUniqueTogether(
            name='articlestats',
            unique_together=set([(b'datetime', b'ad_group', b'article', b'source'), (b'datetime', b'ad_group', b'article', b'network')]),
        ),
    ]
