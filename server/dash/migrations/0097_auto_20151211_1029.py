# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0096_auto_20151210_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publisherblacklist',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.Source', null=True),
        ),
    ]
