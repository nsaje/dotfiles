# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0011_auto_20150217_0933'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='batch',
        ),
        migrations.RemoveField(
            model_name='article',
            name='image_id',
        ),
    ]
