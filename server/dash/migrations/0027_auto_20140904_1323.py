# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0026_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZemantaExclusivePublishers',
            fields=[
                ('exclusive_publisher_ids', models.TextField(blank=True)),
                ('source', models.OneToOneField(primary_key=True, serialize=False, to='dash.Source')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaignsettings',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterModelOptions(
            name='defaultsourcecredentials',
            options={'verbose_name_plural': b'Default Source Credentials'},
        ),
    ]
