# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0049_remove_source_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceAction',
            fields=[
                ('action', models.IntegerField(serialize=False, primary_key=True, choices=[(3, b'Can update daily budget'), (1, b'Can update state'), (2, b'Can update CPC')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
