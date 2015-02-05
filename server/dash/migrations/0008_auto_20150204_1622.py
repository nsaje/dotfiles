# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_account_outbrain_account'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='outbrain_account',
        ),
        migrations.RemoveField(
            model_name='outbrainaccount',
            name='name',
        ),
        migrations.AddField(
            model_name='outbrainaccount',
            name='used',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
