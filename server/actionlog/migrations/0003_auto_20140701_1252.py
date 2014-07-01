# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0002_auto_20140626_1615'),
    ]

    operations = [
        migrations.RenameField(
            model_name='actionlog',
            old_name='created_datetime',
            new_name='created_dt',
        ),
        migrations.RenameField(
            model_name='actionlog',
            old_name='modified_datetime',
            new_name='modified_dt',
        ),
    ]
