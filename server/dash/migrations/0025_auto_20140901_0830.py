# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0024_auto_20140828_1629'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultSourceCredentials',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('credentials', models.ForeignKey(to='dash.SourceCredentials', on_delete=django.db.models.deletion.PROTECT)),
                ('source', models.ForeignKey(to='dash.Source', on_delete=django.db.models.deletion.PROTECT, unique=True)),
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
    ]
