# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_auto_20151216_0839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplyreportrecipient',
            name='email',
            field=models.EmailField(max_length=255, verbose_name=b'email address'),
        ),
    ]
