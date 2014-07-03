# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0006_auto_20140702_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlog',
            name='message',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
    ]
