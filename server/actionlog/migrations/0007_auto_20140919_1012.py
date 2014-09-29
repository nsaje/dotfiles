# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0006_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
