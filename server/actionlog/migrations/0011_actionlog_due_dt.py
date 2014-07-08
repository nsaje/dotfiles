# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import actionlog.models


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0010_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlog',
            name='due_dt',
            field=models.DateTimeField(default=actionlog.models._due_date_default, null=True, blank=True),
            preserve_default=True,
        ),
    ]
