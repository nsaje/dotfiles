# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0026_auto_20150331_1215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='content_ad',
        ),
        migrations.AlterField(
            model_name='contentad',
            name='ad_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        )
    ]
