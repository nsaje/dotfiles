# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0008_auto_20140703_1456'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actionlogorder',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='actionlogorder',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='actionlogorder',
            name='modified_dt',
        ),
        migrations.RemoveField(
            model_name='actionlogorder',
            name='state',
        ),
    ]
