# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0041_adgroup_is_demo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoadgrouprealadgroup',
            name='demo_ad_group',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', unique=True),
        ),
    ]
