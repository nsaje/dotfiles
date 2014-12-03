# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0008_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='created_dt',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='modified_dt',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name=b'Modified at', db_index=True),
        ),
    ]
