# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0081_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='publisherblacklist',
            name='account',
            field=models.ForeignKey(related_name='account', on_delete=django.db.models.deletion.PROTECT, to='dash.Account', null=True),
        ),
        migrations.AddField(
            model_name='publisherblacklist',
            name='campaign',
            field=models.ForeignKey(related_name='campaign', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign', null=True),
        ),
        migrations.AddField(
            model_name='publisherblacklist',
            name='everywhere',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='publisherblacklist',
            unique_together=set([('name', 'everywhere', 'account', 'campaign', 'ad_group', 'source')]),
        ),
    ]
