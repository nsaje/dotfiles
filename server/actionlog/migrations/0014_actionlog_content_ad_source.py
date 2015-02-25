# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0018_auto_20150225_1353'),
        ('actionlog', '0013_auto_20150224_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlog',
            name='content_ad_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.ContentAdSource', null=True),
            preserve_default=True,
        ),
    ]
