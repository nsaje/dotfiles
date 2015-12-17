# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0003_auto_20151215_1353'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='conversiongoal',
            unique_together=set([('campaign', 'type', 'goal_id'), ('campaign', 'name')]),
        ),
    ]
