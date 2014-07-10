
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0013_auto_20140710_0926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='payload',
            field=jsonfield.fields.JSONField(default={}, blank=True),
        ),
    ]
