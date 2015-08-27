# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0066_auto_20150826_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversionpixel',
            name='account',
            field=models.ForeignKey(to='dash.Account', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
