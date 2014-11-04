# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0043_auto_20141030_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoadgrouprealadgroup',
            name='real_ad_group',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup', unique=True),
        ),
    ]
