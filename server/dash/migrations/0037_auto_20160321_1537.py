# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_auto_20160321_1515'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='landing_mode',
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='landing_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='created_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
