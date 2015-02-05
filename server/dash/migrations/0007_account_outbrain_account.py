# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0006_outbrainaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='outbrain_account',
            field=models.ForeignKey(to='dash.OutbrainAccount', null=True),
            preserve_default=True,
        ),
    ]
