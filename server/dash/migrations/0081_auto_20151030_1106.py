# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0080_merge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='budgethistory',
            old_name='state',
            new_name='snapshot',
        ),
        migrations.RenameField(
            model_name='credithistory',
            old_name='state',
            new_name='snapshot',
        ),
    ]
