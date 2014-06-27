# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20140627_1121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articlestats',
            name='cpc_cc',
        ),
    ]
