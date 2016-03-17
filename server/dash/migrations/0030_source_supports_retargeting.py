# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0029_auto_20160303_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='supports_retargeting',
            field=models.BooleanField(default=False, help_text='Designates whether source supports retargeting.'),
        ),
    ]
