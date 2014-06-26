# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_articlestats'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlestats',
            name='cost',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=4),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='cpc',
            field=models.DecimalField(default=0, max_digits=10, decimal_places=4),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='articlestats',
            name='cost_cc',
        ),
        migrations.RemoveField(
            model_name='articlestats',
            name='cpc_cc',
        ),
    ]
