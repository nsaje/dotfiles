# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import __builtin__
import jsonfield.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0027_auto_20140904_1323'),
        ('dash', '0028_auto_20140904_0648'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DefaultSourceCredentials',
            new_name='DefaultSourceSettings',
        ),
        migrations.RemoveField(
            model_name='zemantaexclusivepublishers',
            name='source',
        ),
        migrations.DeleteModel(
            name='ZemantaExclusivePublishers',
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
