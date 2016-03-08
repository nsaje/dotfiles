# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0028_campaign_landing_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='modified_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
