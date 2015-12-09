# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def default_allowed_sources(apps, schema_editor):
    return # I dropped the allowed_sources on account settings - tomazk

class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0092_merge'),
    ]

    operations = [
        migrations.RunPython(default_allowed_sources),
    ]
