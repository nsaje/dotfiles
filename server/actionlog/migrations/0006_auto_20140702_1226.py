# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0005_actionlog'),
    ]

    operations = [
        migrations.RenameField(
            model_name='actionlog',
            old_name='action_status',
            new_name='state',
        ),
    ]
