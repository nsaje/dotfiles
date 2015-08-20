# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0064_remove_sourcetype_available_actions_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentad',
            name='brand_name',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='call_to_action',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='description',
            field=models.CharField(default=b'', max_length=140, blank=True),
        ),
        migrations.AddField(
            model_name='contentad',
            name='display_url',
            field=models.CharField(default=b'', max_length=25, blank=True),
        ),
    ]
