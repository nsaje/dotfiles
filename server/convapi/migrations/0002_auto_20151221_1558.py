# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gareportlog',
            name='recipient',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='reportlog',
            name='recipient',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]
