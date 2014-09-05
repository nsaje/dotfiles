# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0028_auto_20140904_1514'),
    ]

    operations = [
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
            name='defaultsourcesettings',
            options={'verbose_name_plural': b'Default Source Settings'},
        ),
        migrations.AddField(
            model_name='defaultsourcesettings',
            name='params',
            field=jsonfield.fields.JSONField(default={}, verbose_name=b'Additional action parameters', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='defaultsourcesettings',
            name='credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='dash.SourceCredentials', null=True),
        ),
    ]
