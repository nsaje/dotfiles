# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0046_sourcetype'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='source_type',
            field=models.ForeignKey(to='dash.SourceType', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sourcetype',
            name='type',
            field=models.CharField(unique=True, max_length=127),
        ),
    ]
