# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0051_source_action_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcetype',
            name='available_actions',
            field=models.ManyToManyField(to='dash.SourceAction', blank=True),
            preserve_default=True,
        ),
    ]
