# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('convapi', '0005_auto_20141203_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='gareportlog',
            name='multimatch',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gareportlog',
            name='multimatch_clicks',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gareportlog',
            name='nomatch',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
