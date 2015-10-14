# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0078_useractionlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublisherBlacklist',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('ad_group', models.ForeignKey(related_name='ad_group', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup')),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='publisherblacklist',
            unique_together=set([('name', 'ad_group', 'source')]),
        ),
    ]
