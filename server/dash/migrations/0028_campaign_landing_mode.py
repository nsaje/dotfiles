# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0027_sourcetype_budgets_tz'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='landing_mode',
            field=models.BooleanField(default=False),
        ),
    ]
