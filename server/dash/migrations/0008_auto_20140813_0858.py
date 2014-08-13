# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0007_auto_20140812_0804'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={},
        ),
        migrations.AlterModelOptions(
            name='adgroup',
            options={},
        ),
        migrations.AlterModelOptions(
            name='campaign',
            options={},
        ),
        migrations.AddField(
            model_name='account',
            name='groups',
            field=models.ManyToManyField(to=b'auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaign',
            name='groups',
            field=models.ManyToManyField(to=b'auth.Group'),
            preserve_default=True,
        ),
    ]
