# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
        ('zemauth', '0003_auto_20140811_1139'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Permission', on_delete=django.db.models.deletion.PROTECT, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
