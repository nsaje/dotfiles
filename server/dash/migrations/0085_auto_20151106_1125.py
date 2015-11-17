# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0084_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publisherblacklist',
            name='ad_group',
            field=models.ForeignKey(related_name='ad_group', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', null=True),
        ),
    ]
